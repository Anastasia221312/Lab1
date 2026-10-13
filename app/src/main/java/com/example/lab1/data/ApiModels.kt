package com.example.lab1.data

import com.google.gson.annotations.SerializedName

// ---------- Запит ----------
data class PlanRequestDto(
    val age: Int,
    val sex: String,               // "male" | "female"
    @SerializedName("weight_kg") val weightKg: Double,
    @SerializedName("height_cm") val heightCm: Double,
    val activity: String,          // "sedentary" | "light" | "moderate" | "high"
    val goal: String,              // "lose" | "maintain" | "gain"
    val excluded: List<String>,
)

// ---------- Відповідь (усі поля nullable: Gson не перевіряє null-безпеку Kotlin) ----------
data class PlanResponseDto(
    val calories: CaloriesDto?,
    val meals: List<MealDto>?,
    @SerializedName("total_kcal") val totalKcal: Int?,
    @SerializedName("deviation_pct") val deviationPct: Double?,
    val source: String?,
    val warnings: List<String>?,
    val disclaimer: String?,
)

data class CaloriesDto(val bmr: Int?, val tdee: Int?, val target: Int?)
data class MealDto(val name: String?, val items: List<MealItemDto>?, val kcal: Int?)
data class MealItemDto(val name: String?, val grams: Int?, val kcal: Int?)

// ---------- Помилка від backend: {"error": {"code": "...", "message": "..."}} ----------
data class ErrorEnvelopeDto(val error: ErrorBodyDto?)
data class ErrorBodyDto(val code: String?, val message: String?)

// ---------- Внутрішня (доменна) модель, яку бачить UI ----------
data class PlanData(
    val bmr: Int,
    val tdee: Int,
    val target: Int,
    val meals: List<MealData>,
    val totalKcal: Int,
    val deviationPct: Double,
    val aiSource: Boolean,         // true = Gemini, false = базовий алгоритм
    val warnings: List<String>,
    val disclaimer: String,
)

data class MealData(val name: String, val items: List<MealItemData>, val kcal: Int)
data class MealItemData(val name: String, val grams: Int, val kcal: Int)

/** Помилка з повідомленням, яке можна показати користувачу. */
class PlanException(message: String) : Exception(message)
