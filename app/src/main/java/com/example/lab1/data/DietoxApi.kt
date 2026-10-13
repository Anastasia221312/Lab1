package com.example.lab1.data

import java.util.concurrent.TimeUnit
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface DietoxApi {
    @GET("health")
    suspend fun health(): Map<String, String>

    @POST("plan")
    suspend fun createPlan(@Body request: PlanRequestDto): PlanResponseDto
}

object ApiClient {
    val api: DietoxApi by lazy {
        val http = OkHttpClient.Builder()
            .connectTimeout(ApiConfig.TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .readTimeout(ApiConfig.TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .build()
        Retrofit.Builder()
            .baseUrl(ApiConfig.BASE_URL)
            .client(http)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(DietoxApi::class.java)
    }
}
