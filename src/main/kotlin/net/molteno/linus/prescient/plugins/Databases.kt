package net.molteno.linus.prescient.plugins

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.datetime.Instant
import kotlinx.datetime.TimeZone
import kotlinx.datetime.toLocalDateTime
import net.molteno.linus.prescient.sources.sdo.database.SdoSchema
import net.molteno.linus.prescient.sources.swpc.database.SwpcRegionSchema
import org.jetbrains.exposed.sql.Database
import java.sql.DriverManager
import java.util.*

fun Application.configureDatabases(): Database {
    val db = connectToPostgres(embedded = environment.developmentMode)
    val sdo = SdoSchema(db)
    val swpcRegions = SwpcRegionSchema(db)

    routing {
        get("/sdo/hmi") {
            try {
                val start = call.request.queryParameters["start"]?.let { Instant.parse(it) }
                val end = call.request.queryParameters["end"]?.let { Instant.parse(it) }

                if (start != null && end != null) {
                    val observations = sdo.read(start, end)
                    call.respond(HttpStatusCode.OK, observations)
                } else {
                    call.respond(HttpStatusCode.BadRequest)
                }
            } catch (e: IllegalArgumentException) {
                call.respond(HttpStatusCode.BadRequest)
            }
        }

        get("/sdo/hmi/latest") {
            val observation = sdo.readLatest()
            if (observation != null) {
                call.respond(HttpStatusCode.OK, observation)
            } else {
                call.respond(HttpStatusCode.NoContent)
            }
        }

        get("/swpc/region") {
            try {
                val start = call.request.queryParameters["start"]?.let { Instant.parse(it).toLocalDateTime(TimeZone.UTC).date }
                val end = call.request.queryParameters["end"]?.let { Instant.parse(it).toLocalDateTime(TimeZone.UTC).date }

                if (start != null && end != null) {
                    val observations = swpcRegions.read(start, end)
                    call.respond(HttpStatusCode.OK, observations)
                } else {
                    call.respond(HttpStatusCode.BadRequest)
                }
            } catch (e: IllegalArgumentException) {
                call.respond(HttpStatusCode.BadRequest)
            }
        }

        get("/swpc/region/{region}") {
            try {
                val regionId = call.parameters["region"]?.toIntOrNull()

                if (regionId != null) {
                    val observations = swpcRegions.readRegion(regionId)
                    call.respond(HttpStatusCode.OK, observations)
                } else {
                    call.respond(HttpStatusCode.BadRequest)
                }
            } catch (e: IllegalArgumentException) {
                call.respond(HttpStatusCode.BadRequest)
            }
        }
    }

    return db
}

fun Application.connectToPostgres(embedded: Boolean): Database {
    Class.forName("org.postgresql.Driver")
    if (embedded) {
        return Database.connect({ DriverManager.getConnection("jdbc:h2:mem:test;DB_CLOSE_DELAY=-1", "root", "") })
    } else {
        val url = environment.config.property("postgres.url").getString()

        val properties = Properties().apply {
            setProperty("user", environment.config.property("postgres.user").getString())
            setProperty("reWriteBatchedInserts", "true")
        }

        return Database.connect({ DriverManager.getConnection(url, properties) })
    }
}
