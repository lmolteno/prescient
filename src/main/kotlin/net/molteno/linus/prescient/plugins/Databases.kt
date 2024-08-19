package net.molteno.linus.prescient.plugins

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.datetime.Instant
import kotlinx.serialization.ExperimentalSerializationApi
import net.molteno.linus.prescient.sources.sdo.database.SdoSchema
import org.jetbrains.exposed.sql.Database
import java.sql.DriverManager
import java.util.*

@OptIn(ExperimentalSerializationApi::class)
fun Application.configureDatabases(): Database {
    val db = connectToPostgres(embedded = environment.developmentMode)
    val sdo = SdoSchema(db)

    routing {
        get("/hmi") {
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
