package net.molteno.linus.prescient.sources.swpc

import io.ktor.server.application.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import net.molteno.linus.prescient.sources.sdo.LOGGER
import net.molteno.linus.prescient.sources.swpc.database.SwpcRegionSchema
import org.jetbrains.exposed.sql.Database
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

fun Application.configureSwpcFetchJob(db: Database) {
    val schema = SwpcRegionSchema(db)

    launch(Dispatchers.IO) {
        LOGGER.debug("Launching Solar Region Fetch JOb")

        while (true) {
            LOGGER.info("Fetching regions from SWPC...")

            val regions = try {
                getSolarRegions()
            } catch (e: Exception) {
                LOGGER.error("Failed to fetch regions from SWPC", e)
                delay(1.seconds)
                continue
            }

            schema.create(regions)
            LOGGER.info("Inserted {} regions from SWPC...", regions.size)

            delay(5.minutes)
        }
    }
}
