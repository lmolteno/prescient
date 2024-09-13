package net.molteno.linus.prescient.sources.sdo.database

import kotlinx.coroutines.Dispatchers
import kotlinx.datetime.Instant
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import net.molteno.linus.prescient.sources.sdo.Contour
import net.molteno.linus.prescient.sources.sdo.database.SdoSchema.HmiObservation.observationTime
import net.molteno.linus.prescient.sources.sdo.database.SdoSchema.HmiObservation.penumbraContours
import net.molteno.linus.prescient.sources.sdo.database.SdoSchema.HmiObservation.processedTime
import net.molteno.linus.prescient.sources.sdo.database.SdoSchema.HmiObservation.umbraContours
import org.jetbrains.exposed.sql.*
import org.jetbrains.exposed.sql.json.json
import org.jetbrains.exposed.sql.kotlin.datetime.timestamp
import org.jetbrains.exposed.sql.transactions.experimental.newSuspendedTransaction
import org.jetbrains.exposed.sql.transactions.transaction

@Serializable
data class SdoHmiObservation(
    val observed: Instant,
    val processed: Instant,
    val umbraContours: List<Contour>,
    val penumbraContours: List<Contour>,
)

@Serializable
data class SdoHmiObservationWithId(
    val id: Int,
    val observed: Instant,
    val processed: Instant,
    val umbraContours: List<Contour>,
    val penumbraContours: List<Contour>,
)

class SdoSchema(database: Database) {
    object HmiObservation : Table() {
        val id = integer("id").autoIncrement()
        val observationTime = timestamp("observation_time").uniqueIndex()
        val processedTime = timestamp("processed_time")
        val umbraContours = json<List<Contour>>("umbra_contours", serialize = { Json.encodeToString(it) }, deserialize = { Json.decodeFromString(it) })
        val penumbraContours = json<List<Contour>>("penumbra_contours", serialize = { Json.encodeToString(it) }, deserialize = { Json.decodeFromString(it) })

        override val primaryKey = PrimaryKey(id)
    }

    init {
        transaction(database) { SchemaUtils.create(HmiObservation) }
    }

    private suspend fun <T> dbQuery(block: suspend () -> T): T =
        newSuspendedTransaction(Dispatchers.IO) { block() }

    suspend fun create(observation: SdoHmiObservation): Int = dbQuery {
        HmiObservation.insert {
            it[observationTime] = observation.observed
            it[processedTime] = observation.processed
            it[umbraContours] = observation.umbraContours
            it[penumbraContours] = observation.penumbraContours
        }[HmiObservation.id]
    }

    suspend fun read(obsTime: Instant): SdoHmiObservationWithId? = dbQuery {
        HmiObservation.selectAll()
            .where { observationTime.eq(obsTime) }
            .limit(1)
            .map {
                SdoHmiObservationWithId(
                    it[HmiObservation.id],
                    it[observationTime],
                    it[processedTime],
                    it[umbraContours],
                    it[penumbraContours]
                )
            }
            .firstOrNull()
    }

    suspend fun read(start: Instant, end: Instant): List<SdoHmiObservationWithId> = dbQuery {
        HmiObservation.selectAll().where { observationTime.between(start, end) }.map {
            SdoHmiObservationWithId(
                it[HmiObservation.id],
                it[observationTime],
                it[processedTime],
                it[umbraContours],
                it[penumbraContours]
            )
        }
    }

    suspend fun getLatestObservation(): Instant? = dbQuery {
        HmiObservation
            .select(observationTime)
            .orderBy(observationTime to SortOrder.DESC)
            .limit(1)
            .map { it[observationTime] }
            .firstOrNull()
    }
}
