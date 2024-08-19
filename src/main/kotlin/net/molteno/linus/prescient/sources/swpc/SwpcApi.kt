package net.molteno.linus.prescient.sources.swpc

import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonNamingStrategy
import net.molteno.linus.prescient.sources.swpc.models.*

@OptIn(ExperimentalSerializationApi::class)
private val client = HttpClient(CIO) {
    install(ContentNegotiation) { json(Json {
        namingStrategy = JsonNamingStrategy.SnakeCase
        ignoreUnknownKeys = true
    }) }
    install(HttpTimeout) { requestTimeoutMillis = 60_000 }
}

private const val BASE_URL = "https://services.swpc.noaa.gov/"

suspend fun getSolarRegions(): List<SolarRegionObservation> {
    val regions: List<SolarRegionObservationDto> = client.get("$BASE_URL/json/solar_regions.json").body()
    return regions.mapNotNull { it.toSolarRegionObservation() }
}

suspend fun getSolarEvents(): List<SolarEventObservation> {
    val regions: List<SolarEventObservationDto> = client.get("$BASE_URL/json/edited_events.json").body()
    return regions.mapNotNull { it.toSolarEventObservation() }
}
