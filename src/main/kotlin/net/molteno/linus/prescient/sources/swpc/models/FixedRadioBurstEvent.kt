package net.molteno.linus.prescient.sources.swpc.models

import kotlinx.datetime.Instant

data class FixedRadioBurstEvent(
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

    val frequency: Int,
    /**
     * 	The peak value above pre-burst background of associated radio bursts
     * 	at frequencies 245, 410, 610, 1415, 2695, 4995, 8800 and 15400 MHz:
     * 	       1 flux unit = 10-22 Wm-2 Hz-1
     */
    val maxBrightness: Int
): SolarEventObservation
