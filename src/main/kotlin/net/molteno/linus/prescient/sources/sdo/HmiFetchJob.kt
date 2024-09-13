package net.molteno.linus.prescient.sources.sdo

import io.github.reactivecircus.cache4k.Cache
import io.ktor.server.application.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.datetime.Clock
import kotlinx.datetime.Instant
import net.molteno.linus.prescient.sources.sdo.database.SdoHmiObservation
import net.molteno.linus.prescient.sources.sdo.database.SdoSchema
import org.jetbrains.exposed.sql.Database
import kotlin.time.Duration.Companion.days
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

fun Application.configureHmiFetchJob(db: Database) {
    val schema = SdoSchema(db)

    launch(Dispatchers.IO) {
        LOGGER.debug("Launching HMI Fetch Job")

        var observationTime = schema.getLatestObservation() ?: Clock.System.now().previousQuarterHour().minus(7.days + 15.minutes)

        val latestTimeCache = Cache.Builder<String, Instant>()
            .expireAfterWrite(10.seconds)
            .build()

        while (true) {
            val latestTime = try {
                latestTimeCache.get("latestTime", {
                    var time = getLatestTime()
                    while (time == null) {
                        delay(10.seconds)
                        time = getLatestTime()
                    }
                    return@get time
                })
            } catch (e: Throwable) {
                LOGGER.error("Failed to fetch latestTime", e)
                continue
            }

            if (observationTime.plus(15.minutes) < latestTime) {
                observationTime += 15.minutes
            } else {
                observationTime = latestTime
            }

            LOGGER.info("Running with an observation time of {}", observationTime)
            if (schema.read(observationTime) != null) {
                if (observationTime >= latestTime) {
                    delay(1.minutes)
                }
                continue
            }
            val image = try {
                getHmiImage(observationTime, ImageScale.Big)
            } catch (e: Throwable) {
                LOGGER.error("Failed to fetch for observation at {}", observationTime, e)
                delay(1.seconds)
                continue
            }

            if (image != null) {
                LOGGER.info("Fetched observation for {}", observationTime)
                schema.create(
                    SdoHmiObservation(
                        observed = observationTime,
                        processed = Clock.System.now(),
                        umbraContours = image.umbra,
                        penumbraContours = image.penumbra
                    )
                )
            } else {
                LOGGER.debug("Found no existing observation for {}", observationTime)
            }
        }
    }
}
