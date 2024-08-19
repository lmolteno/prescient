package net.molteno.linus.prescient.sources.swpc.models

import kotlinx.datetime.Instant
import kotlinx.serialization.Serializable

@Serializable
data class SolarEventObservationDto (
        val beginDatetime: String?,
        val beginQuality: String?,
        val maxDatetime: String?,
        val maxQuality: String?,
        val endDatetime: String?,
        val endQuality: String?,
        val observatory: String,
        val quality: String,
        val type: String,
        val codedType: Int,
        val obsid: Int,
        val location: String,
        val frequency: String,
        val particulars1: String?,
        val particulars2: String?,
        val particulars3: String?,
        val particulars4: String?,
        val particulars5: String?,
        val particulars6: String?,
        val particulars7: String?,
        val particulars8: String?,
        val particulars9: String?,
        val particulars10: String,
        val region: Int?,
        val bin: Int,
        val age: String?,
        val statusCode: Int,
        val statusText: String,
        val changeFlag: Int
    )

interface SolarEventObservation {
    val region: Int?
    val eventId: Int

    /**
    The begin time of an x-ray event is defined as the first minute in a
    sequence of 4 minutes of steep monotonic increase in 0.1-0.8 nm flux.
    The x-ray event maximum is taken as the minute of the peak x-ray flux.
    The end time is the time when the flux level decays to a point halfway
    between the maximum flux and the pre-flare background level.

    The begin time of an SXI flare (XFL) is minutes following the associated
    x-ray event. The maximum time is the most intense period in the brightest
    region of the SXI image. The end time is the last SXI image before the X-ray
    event end time.
     */
    val beginDatetime: Instant
    val beginQuality: String?

    val maxDatetime: Instant?
    val maxQuality: String?

    val endDatetime: Instant?
    val endQuality: String?

    val type: SolarEventType
    val observatory: SolarObservatory
    val quality: String?

    val statusCode: Int
    val statusText: String
    val changeFlag: Int
}

data class GenericSolarEvent(
    override val region: Int?,
    override val eventId: Int,

    /**
        The begin time of an x-ray event is defined as the first minute, in a
        sequence of 4 minutes, of steep monotonic increase in 0.1-0.8 nm flux.
        The x-ray event maximum is taken as the minute of the peak x-ray flux.
        The end time is the time when the flux level decays to a point halfway
        between the maximum flux and the pre-flare background level.

        The begin time of an SXI flare (XFL) is minutes following the associated
        x-ray event. The maximum time is the most intense period in the brightest
        region of the SXI image. The end time is the last SXI image before the X-ray
        event end time.
     */
    override val beginDatetime: Instant,
    override val beginQuality: String?,

    override val maxDatetime: Instant?,
    override val maxQuality: String?,

    override val endDatetime: Instant?,
    override val endQuality: String?,

    override val type: SolarEventType,
    override val observatory: SolarObservatory,
    override val quality: String?,

    override val statusCode: Int,
    override val statusText: String,
    override val changeFlag: Int
): SolarEventObservation

enum class SolarEventType(val code: String) {
    BrightSurge("BSL"),
    FilamentDisappearance("DSF"),
    EruptiveProminence("EPL"),
    Filament("FIL"),
    OpticalFlare("FLA"),
    ForbushDecrease("FOR"),
    GroundLevelEvent("GLE"),
    LoopProminenceSystem("LPS"),
    PolarCapAbsorption("PCA"),
    FixedFrequencyRadioBurst("RBR"),
    RadioNoiseStorm("RNS"),
    SweepFrequencyRadioBurst("RSP"),
    Spray("SPY"),
    XRayFlare("XFL"),
    XRayEvent("XRA"),
}

enum class SolarObservatory(val code: String) {
    Culgoora("CUL"),
    Holloman("HOL"),
    Palahua("PAL"),
    Learmonth("LEA"),
    Ramey("RAM"),
    SagamoreHill("SAG"),
    SanVito("SVI"),
    Goes13("G13"),
    Goes14("G14"),
    Goes15("G15"),
    Goes16("G16"),
    Goes17("G17"),
    Goes18("G18"),
    Goes19("G19"),
}

fun SolarEventObservationDto.toSolarEventObservation(): SolarEventObservation? {
    val particulars = listOf(particulars1, particulars2, particulars3, particulars4, particulars5, particulars6, particulars7, particulars8, particulars9, particulars10)
    val type = SolarEventType.entries.firstOrNull { it.code == type }
    if (type == null) {
//        Timber.d("Unknown event type: ${this.type}")
        return null
    }

    val observatory = SolarObservatory.entries.firstOrNull { it.code == observatory }
    if (observatory == null) {
//        Timber.d("Unknown observatory: ${this.observatory}")
        return null
    }

    val beginDatetime = Instant.parse(beginDatetime ?: return null)
    val maxDatetime = if (maxDatetime == null) null else Instant.parse(maxDatetime)
    val endDatetime = if (endDatetime == null ) null else Instant.parse(endDatetime)

    when (type) {
        SolarEventType.XRayEvent -> {
            if (particulars1 == null) return null

            return XrayEvent(
                beginDatetime = beginDatetime,
                beginQuality = beginQuality,
                maxDatetime = maxDatetime,
                maxQuality = maxQuality,
                endDatetime = endDatetime,
                endQuality = endQuality,
                observatory = observatory,
                quality = quality,
                type = type,
                frequency = frequency,
                region = region,
                eventId = bin,
                statusCode = statusCode,
                statusText = statusText,
                changeFlag = changeFlag,
                xRayClass = particulars1,
            )
        }
        SolarEventType.OpticalFlare -> {
            if (particulars1 == null || particulars1.length < 2) return null
            val characteristics = particulars.filterNotNull().map {
                try { FlareEvent.FlareCharacteristic.valueOf(it) }
                catch (e: IllegalArgumentException) { null }
            }.filterNotNull()

            try {
                return FlareEvent(
                    beginDatetime = beginDatetime,
                    beginQuality = beginQuality,
                    maxDatetime = maxDatetime,
                    maxQuality = maxQuality,
                    endDatetime = endDatetime,
                    endQuality = endQuality,
                    observatory = observatory,
                    quality = quality,
                    type = type,
                    region = region,
                    eventId = bin,
                    statusCode = statusCode,
                    statusText = statusText,
                    changeFlag = changeFlag,
                    location = location,
                    importance = particulars1.first(),
                    characteristics = characteristics,
                    brightness = FlareEvent.FlareBrightness.valueOf(particulars1.substring(1)),
                )
            } catch (e: IllegalArgumentException) {
                return null
            }
        }
        SolarEventType.FixedFrequencyRadioBurst -> {
            if (particulars1 == null) return null
            val frequencyInt = frequency.toIntOrNull() ?: return null

            return FixedRadioBurstEvent(
                beginDatetime = beginDatetime,
                beginQuality = beginQuality,
                maxDatetime = maxDatetime,
                maxQuality = maxQuality,
                endDatetime = endDatetime,
                endQuality = endQuality,
                observatory = observatory,
                quality = quality,
                type = type,
                region = region,
                eventId = bin,
                statusCode = statusCode,
                statusText = statusText,
                changeFlag = changeFlag,
                frequency = frequencyInt,
                maxBrightness = particulars1.toIntOrNull() ?: return null
            )
        }
        SolarEventType.SweepFrequencyRadioBurst -> {
            val frequencyInt = frequency.split('-').map { it.toIntOrNull() ?: return null }
            if (frequencyInt.size != 2) return null
            val frequencyRange = frequencyInt[0]..frequencyInt[1]

            if (particulars1 == null) return null
            val (burstTypeStr, intensity) = particulars1.split('/')
            val intensityInt = intensity.toIntOrNull() ?: return null
            val burstType = try { SweptRadioBurstEvent.RadioBurstType.valueOf(burstTypeStr) }
                            catch (e: IllegalArgumentException) { return null }


            return SweptRadioBurstEvent(
                beginDatetime = beginDatetime,
                beginQuality = beginQuality,
                maxDatetime = maxDatetime,
                maxQuality = maxQuality,
                endDatetime = endDatetime,
                endQuality = endQuality,
                observatory = observatory,
                quality = quality,
                type = type,
                region = region,
                eventId = bin,
                statusCode = statusCode,
                statusText = statusText,
                changeFlag = changeFlag,
                frequencyRange = frequencyRange,
                intensity = intensityInt,
                radioBurstType = burstType,
            )
        }
//        SolarEventType.RadioNoiseStorm -> TODO()
//        SolarEventType.Spray -> TODO()
//        SolarEventType.XRayFlare -> TODO()
//        SolarEventType.BrightSurge -> TODO()
//        SolarEventType.FilamentDisappearance -> TODO()
//        SolarEventType.EruptiveProminence -> TODO()
//        SolarEventType.Filament -> TODO()
//        SolarEventType.ForbushDecrease -> TODO()
//        SolarEventType.GroundLevelEvent -> TODO()
//        SolarEventType.LoopProminenceSystem -> TODO()
//        SolarEventType.PolarCapAbsorption -> TODO()
        else -> {
            return GenericSolarEvent(
                beginDatetime = beginDatetime,
                beginQuality = beginQuality,
                maxDatetime = maxDatetime,
                maxQuality = maxQuality,
                endDatetime = endDatetime,
                endQuality = endQuality,
                observatory = observatory,
                quality = quality,
                type = type,
                region = region,
                eventId = bin,
                statusCode = statusCode,
                statusText = statusText,
                changeFlag = changeFlag,
            )
        }
    }
}

/*
{
    "begin_datetime": "2024-05-28T06:38:00",
    "begin_quality": "",
    "max_datetime": "2024-05-28T06:43:00",
    "max_quality": "",
    "end_datetime": "2024-05-28T06:48:00",
    "end_quality": "",
    "observatory": "G16",
    "quality": "5",
    "type": "XRA",
    "coded_type": 1,
    "obsid": 0,
    "location": "",
    "frequency": "1-8A",
    "particulars1": "C4.1",
    "particulars2": "1.4E-03",
    "particulars3": null,
    "particulars4": null,
    "particulars5": null,
    "particulars6": null,
    "particulars7": null,
    "particulars8": null,
    "particulars9": null,
    "particulars10": "4.1E-06",
    "region": 3697,
    "bin": 7000,
    "age": null,
    "status_code": 5,
    "status_text": "",
    "change_flag": 0
  },
 */
