package com.anekdot.vtemu

import android.app.Application
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.util.concurrent.TimeUnit

class AnekdotApp : Application() {

    lateinit var retrofit: Retrofit
        private set

    lateinit var anekdotApi: com.anekdot.vtemu.api.AnekdotApi
        private set

    lateinit var repository: com.anekdot.vtemu.repository.AnekdotRepository
        private set

    lateinit var baseUrl: String
        private set

    override fun onCreate() {
        super.onCreate()

        val moshi = Moshi.Builder()
            .addLast(KotlinJsonAdapterFactory())
            .build()

        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BODY
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }

        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()

        baseUrl = if (BuildConfig.DEBUG) {
            BuildConfig.BASE_URL
        } else {
            "https://api.anekdot-vtemu.ru"
        }

        retrofit = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()

        anekdotApi = retrofit.create(com.anekdot.vtemu.api.AnekdotApi::class.java)
        repository = com.anekdot.vtemu.repository.AnekdotRepository(anekdotApi)
    }

    companion object {
        fun getInstance(app: android.app.Application): AnekdotApp {
            return app as AnekdotApp
        }
    }
}
