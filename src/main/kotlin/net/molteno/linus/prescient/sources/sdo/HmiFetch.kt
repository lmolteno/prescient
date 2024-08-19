package net.molteno.linus.prescient.sources.sdo

import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.util.logging.*
import kotlinx.datetime.Instant
import kotlinx.datetime.TimeZone
import kotlinx.datetime.format
import kotlinx.datetime.format.DateTimeComponents
import kotlinx.datetime.format.Padding
import kotlinx.datetime.toLocalDateTime
import kotlinx.serialization.KSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.FloatArraySerializer
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.descriptors.buildClassSerialDescriptor
import kotlinx.serialization.descriptors.element
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import org.jetbrains.kotlinx.multik.api.linalg.dot
import org.jetbrains.kotlinx.multik.api.mk
import org.jetbrains.kotlinx.multik.api.ndarray
import org.jetbrains.kotlinx.multik.ndarray.data.D1
import org.jetbrains.kotlinx.multik.ndarray.data.slice
import org.opencv.core.CvType.CV_8UC1
import org.opencv.core.Mat
import org.opencv.core.MatOfPoint
import org.opencv.imgcodecs.Imgcodecs
import org.opencv.imgcodecs.Imgcodecs.imdecode
import org.opencv.imgproc.Imgproc.*
import kotlin.math.abs
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.nanoseconds
import kotlin.time.Duration.Companion.seconds

internal val LOGGER = KtorSimpleLogger("HmiFetch")

object CoordinateSerializer : KSerializer<Coordinate> {
    override val descriptor: SerialDescriptor
        get() =
            buildClassSerialDescriptor("Coordinate") {
                element<Double>("x")
                element<Double>("y")
            }

    override fun deserialize(decoder: Decoder): Coordinate {
        val list = decoder.decodeSerializableValue(FloatArraySerializer())
        return Coordinate(list[0], list[1])
    }

    override fun serialize(encoder: Encoder, value: Coordinate) {
        encoder.encodeSerializableValue(
            FloatArraySerializer(),
            arrayOf(value.x, value.y).toFloatArray()
        )
    }
}

@Serializable(with = CoordinateSerializer::class)
data class Coordinate(val x: Float, val y: Float)

@Serializable
data class Contour(val coordinates: List<Coordinate>) {
    fun area(): Double {
        val first = coordinates.first()
        val last = coordinates.last()
        val correction = last.x * first.y - last.y * first.x
        val x = mk.ndarray(coordinates.map { it.x })
        val y = mk.ndarray(coordinates.map { it.y })
        val size = coordinates.size
        val mainArea = x.slice<Float, D1, D1>(0..size-2).dot(y.slice(1..<size)) -
                y.slice<Float, D1, D1>(0..size-2).dot(x.slice(1..<size))
        return 0.5 * abs(mainArea + correction)
    }

    fun remap(min: Float, max: Float): Contour {
        return this.copy(coordinates = coordinates.map { Coordinate((it.x - min) / (max - min), (it.y - min) / (max - min)) })
    }
}

private fun getMatForImg(img: Mat): Mat {
    val height: Int = img.rows()
    val width: Int = img.cols()
    return Mat(height, width, CV_8UC1)
}

private fun getContours(im: Mat, threshold: Double): List<Contour> {
    val thresh = getMatForImg(im)
    threshold(im, thresh, threshold * 255, 255.0, 0)
    val contours = mutableListOf<MatOfPoint>()

    val hierarchy = Mat()
    findContours(thresh, contours, hierarchy, RETR_TREE, CHAIN_APPROX_SIMPLE)

    return contours
        .map { mat -> Contour(mat.toList().map { Coordinate(it.x.toFloat(), it.y.toFloat()) }) }
        .filter { it.coordinates.size >= 3 }
}

const val PENUMBRA_LEVEL = 0.65
const val UMBRA_LEVEL = 0.25
const val SUN_MAX = 3931F
const val SUN_MIN = 162F

@Serializable
data class SunHmiImage(val umbra: List<Contour>, val penumbra: List<Contour>)

val instantFormat = DateTimeComponents.Format {
    year(Padding.ZERO)
    chars("/")
    monthNumber(Padding.ZERO)
    chars("/")
    dayOfMonth(Padding.ZERO)
    chars("/")
    year(Padding.ZERO)
    monthNumber(Padding.ZERO)
    dayOfMonth(Padding.ZERO)
    chars("_")
    hour(Padding.ZERO)
    minute(Padding.ZERO)
    second(Padding.ZERO)
}

val justTimeFormat = DateTimeComponents.Format {
    year(Padding.ZERO)
    monthNumber(Padding.ZERO)
    dayOfMonth(Padding.ZERO)
    chars("_")
    hour(Padding.ZERO)
    minute(Padding.ZERO)
    second(Padding.ZERO)
}

fun Instant.previousQuarterHour(): Instant {
    val utcDate = toLocalDateTime(TimeZone.UTC)
    val currentlyQuarterHour = (utcDate.minute % 15L == 0L) && utcDate.second == 0
    if (currentlyQuarterHour) {
        return this
    }

    return this.minus((utcDate.minute % 15L).minutes)
        .minus(utcDate.second.seconds)
        .minus(utcDate.nanosecond.nanoseconds)
}

@Suppress("unused")
enum class ImageScale(val repr: String, val denominator: Int) {
    Big("4k", 1),
    Medium("1k", 4),
    Small("512", 8),
    ExtraSmall("256", 16)
}

@Serializable
private data class TimesResponse(val first: String, val last: String);

private val client = HttpClient(CIO) {
    install(ContentNegotiation) { json() }
    install(HttpTimeout) { requestTimeoutMillis = 60_000 }
}

suspend fun getLatestTime(): Instant? {
    val res: HttpResponse = client.get("https://jsoc1.stanford.edu/data/hmi/images/image_times.json") {
        expectSuccess = false
    }

    if (res.status == HttpStatusCode.NotFound) {
        return null
    }

    val lastString = res.body<TimesResponse?>()?.last ?: return null
    return Instant.parse(lastString, justTimeFormat)
}

suspend fun getHmiImage(time: Instant, scale: ImageScale): SunHmiImage? {
    val client = HttpClient(CIO) { install(HttpTimeout) { requestTimeoutMillis = 60_000 } }
    val res: HttpResponse = client.get("http://jsoc.stanford.edu/data/hmi/images/${time.format(instantFormat)}_Ic_flat_${scale.repr}.jpg") {
//        onDownload { bytesSentTotal, contentLength ->
//            println("Received $bytesSentTotal bytes from $contentLength")
//        }
        expectSuccess = false
    }

    if (res.status == HttpStatusCode.NotFound) {
        return null
    }

    val jpg = res.body<ByteArray>()
    val jpgMat = Mat(jpg.size, 1, CV_8UC1).apply { put(0, 0, jpg) }
    val img = imdecode(jpgMat, Imgcodecs.IMREAD_GRAYSCALE)
    val penumbraContours = getContours(img, PENUMBRA_LEVEL)
        .filter { (10.0..100_000.0).contains(it.area()) }
        .map { it.remap(SUN_MIN / scale.denominator, SUN_MAX / scale.denominator) }

    val umbraContours = getContours(img, UMBRA_LEVEL)
        .filter { (10.0..100_000.0).contains(it.area()) }
        .map { it.remap(SUN_MIN / scale.denominator, SUN_MAX / scale.denominator) }

    return SunHmiImage(umbraContours, penumbraContours)
}
