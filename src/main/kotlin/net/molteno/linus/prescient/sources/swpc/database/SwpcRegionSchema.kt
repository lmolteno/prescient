package net.molteno.linus.prescient.sources.swpc.database

import kotlinx.coroutines.Dispatchers
import kotlinx.datetime.Instant
import kotlinx.datetime.LocalDate
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import net.molteno.linus.prescient.sources.swpc.database.SwpcRegionSchema.SolarRegion.firstDate
import net.molteno.linus.prescient.sources.swpc.database.SwpcRegionSchema.SolarRegion.id
import net.molteno.linus.prescient.sources.swpc.database.SwpcRegionSchema.SolarRegion.latitude
import net.molteno.linus.prescient.sources.swpc.database.SwpcRegionSchema.SolarRegion.longitude
import net.molteno.linus.prescient.sources.swpc.database.SwpcRegionSchema.SolarRegion.metadata
import net.molteno.linus.prescient.sources.swpc.database.SwpcRegionSchema.SolarRegion.observedDate
import net.molteno.linus.prescient.sources.swpc.database.SwpcRegionSchema.SolarRegion.region
import net.molteno.linus.prescient.sources.swpc.models.SolarRegionObservation
import org.jetbrains.exposed.sql.*
import org.jetbrains.exposed.sql.json.json
import org.jetbrains.exposed.sql.kotlin.datetime.date
import org.jetbrains.exposed.sql.kotlin.datetime.timestamp
import org.jetbrains.exposed.sql.transactions.experimental.newSuspendedTransaction
import org.jetbrains.exposed.sql.transactions.transaction

@Serializable
data class DbSolarRegionObservation(
    val id: Int,
    val region: Int,
    val observedDate: LocalDate, // iso 8601
    val firstDate: Instant,
    val latitude: Int,
    val longitude: Int,
    val metadata: DbSolarRegionObservationMetadata
)

@Serializable
data class DbSolarRegionObservationMetadata(
    val location: String,
    val carringtonLongitude: Int?,
    val area: Int,
    val spotClass: String?,
    val extent: Int,
    val numberSpots: Int,
    val magClass: String?,
    val magString: String?,
    val status: String?,
    val cXrayEvents: Int,
    val mXrayEvents: Int,
    val xXrayEvents: Int,
    val protonEvents: Int?,
    val cFlareProbability: Int,
    val mFlareProbability: Int,
    val xFlareProbability: Int,
    val protonProbability: Int?,
) {
    companion object {
        fun fromSolarRegionObservation(regionObservation: SolarRegionObservation) = DbSolarRegionObservationMetadata(
            regionObservation.location,
            regionObservation.carringtonLongitude,
            regionObservation.area,
            regionObservation.spotClass,
            regionObservation.extent,
            regionObservation.numberSpots,
            regionObservation.magClass,
            regionObservation.magString,
            regionObservation.status,
            regionObservation.cXrayEvents,
            regionObservation.mXrayEvents,
            regionObservation.xXrayEvents,
            regionObservation.protonEvents,
            regionObservation.cFlareProbability,
            regionObservation.mFlareProbability,
            regionObservation.xFlareProbability,
            regionObservation.protonProbability,
        )
    }
}

class SwpcRegionSchema(database: Database) {
    object SolarRegion : Table() {
        val id = integer("id").autoIncrement()
        val observedDate = date("observed_date")
        val region = integer("region")
        val latitude = integer("latitude")
        val longitude = integer("longitude")
        val firstDate = timestamp("first_date")
        val metadata = json<DbSolarRegionObservationMetadata>(
            "metadata",
            serialize = { Json.encodeToString(it) },
            deserialize = { Json.decodeFromString(it) }
        )

        override val primaryKey = PrimaryKey(observedDate, region)
    }

    init {
        transaction(database) {
            SchemaUtils.create(SolarRegion)
        }
    }

    private suspend fun <T> dbQuery(block: suspend () -> T): T =
        newSuspendedTransaction(Dispatchers.IO) { block() }

    suspend fun create(regionObservation: SolarRegionObservation): Int = dbQuery {
        SolarRegion.insert {
            it[region] = regionObservation.region
            it[observedDate] = regionObservation.observedDate
            it[latitude] = regionObservation.latitude
            it[longitude] = regionObservation.longitude
            it[firstDate] = regionObservation.firstDate
            it[metadata] = DbSolarRegionObservationMetadata.fromSolarRegionObservation(regionObservation)
        }[id]
    }

    suspend fun create(regionObservations: List<SolarRegionObservation>): List<Int> = dbQuery {
        SolarRegion.batchUpsert(regionObservations) {
            this[region] = it.region
            this[observedDate] = it.observedDate
            this[latitude] = it.latitude
            this[longitude] = it.longitude
            this[firstDate] = it.firstDate
            this[metadata] = DbSolarRegionObservationMetadata.fromSolarRegionObservation(it)
        }.map { it[id] }
    }

    suspend fun read(start: LocalDate, end: LocalDate) = dbQuery {
        SolarRegion.selectAll()
            .where { observedDate.between(start, end) }
            .orderBy(observedDate)
            .map {
                DbSolarRegionObservation(
                    it[id],
                    it[region],
                    it[observedDate],
                    it[firstDate],
                    it[latitude],
                    it[longitude],
                    it[metadata]
                )
            }
    }

    suspend fun readRegion(regionId: Int) = dbQuery {
        SolarRegion.selectAll()
            .where { region.eq(regionId) }
            .orderBy(observedDate)
            .map {
                DbSolarRegionObservation(
                    it[id],
                    it[region],
                    it[observedDate],
                    it[firstDate],
                    it[latitude],
                    it[longitude],
                    it[metadata]
                )
            }
    }
}
