package net.molteno.linus.prescient.sources.swpc.models

import kotlinx.datetime.Instant

data class XrayEvent(
    override val region: Int?,
    override val eventId: Int,

    override val beginDatetime: Instant,
    override val beginQuality: String?,

    override val maxDatetime: Instant?,
    override val maxQuality: String?,

    override val endDatetime: Instant?,
    override val endQuality: String?,

    override val type: SolarEventType,
    override val observatory: SolarObservatory,
    override val quality: String,

    override val statusCode: Int,
    override val statusText: String,
    override val changeFlag: Int,

    /** MHz */
    val frequency: String,
    val xRayClass: String
): SolarEventObservation