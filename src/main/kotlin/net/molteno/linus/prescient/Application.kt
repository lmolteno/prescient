package net.molteno.linus.prescient

import io.ktor.server.application.*
import io.ktor.server.netty.*
import net.molteno.linus.prescient.plugins.configureDatabases
import net.molteno.linus.prescient.plugins.configureRouting
import net.molteno.linus.prescient.plugins.configureSerialization
import net.molteno.linus.prescient.sources.sdo.configureHmiFetchJob
import net.molteno.linus.prescient.sources.swpc.configureSwpcFetchJob
import org.bytedeco.javacpp.Loader
import org.bytedeco.opencv.opencv_java

fun main(args: Array<String>) {
    Loader.load(opencv_java::class.java)

    return EngineMain.main(args)
}

fun Application.module() {
    configureSerialization()
    val db = configureDatabases()
    configureRouting()
    configureHmiFetchJob(db)
    configureSwpcFetchJob(db)
}
