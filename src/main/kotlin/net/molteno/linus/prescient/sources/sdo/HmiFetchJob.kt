package net.molteno.linus.prescient.sources.sdo

import io.ktor.server.application.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.datetime.Clock
import net.molteno.linus.prescient.sources.sdo.database.SdoHmiObservation
import net.molteno.linus.prescient.sources.sdo.database.SdoSchema
import org.jetbrains.exposed.sql.Database
import kotlin.time.Duration.Companion.days
import kotlin.time.Duration.Companion.minutes

fun Application.configureHmiFetchJob(db: Database) {
    val schema = SdoSchema(db)

    launch(Dispatchers.IO) {
        LOGGER.debug("Launching HMI Fetch JOb")
        var observationTime = Clock.System.now().previousQuarterHour().minus(7.days)

        while (true) {
            LOGGER.info("Running with an observation time of {}", observationTime)
            if (schema.read(observationTime) != null) {
                delay(1.minutes)
                continue
            }
            val image = try {
                getHmiImage(observationTime, ImageScale.Big)
            } catch (_: Throwable) {
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

            val latestTime = getLatestTime() ?: continue

            if (observationTime.plus(15.minutes) < latestTime) {
                observationTime += 15.minutes
            } else {
                observationTime = latestTime
            }
        }
    }
}
