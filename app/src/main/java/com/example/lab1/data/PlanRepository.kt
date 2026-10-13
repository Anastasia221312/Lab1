package com.example.lab1.data

import com.google.gson.Gson
import com.google.gson.JsonParseException
import java.io.IOException
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.HttpException

interface PlanRepository {
    suspend fun createPlan(request: PlanRequestDto): Result<PlanData>
}

class NetworkPlanRepository(
    private val api: DietoxApi = ApiClient.api,
    private val io: CoroutineDispatcher = Dispatchers.IO,
) : PlanRepository {

    override suspend fun createPlan(request: PlanRequestDto): Result<PlanData> = withContext(io) {
        try {
            Result.success(PlanMapper.map(api.createPlan(request)))
        } catch (e: PlanException) {
            Result.failure(e)
        } catch (e: HttpException) {
            Result.failure(PlanException(parseServerError(e)))
        } catch (e: JsonParseException) {
            Result.failure(PlanException("Сервер повернув некоректну відповідь. Спробуйте ще раз."))
        } catch (e: IOException) {
            android.util.Log.e("Dietox", "Network error", e)
            Result.failure(PlanException("Сервер недоступний. Перевірте з'єднання та спробуйте ще раз."))
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            Result.failure(PlanException("Невідома помилка. Спробуйте ще раз."))
        }
    }

    private fun parseServerError(e: HttpException): String {
        val fallback = if (e.code() >= 500) "Помилка сервера. Спробуйте пізніше." else "Сервер відхилив запит."
        return try {
            val body = e.response()?.errorBody()?.string()
            Gson().fromJson(body, ErrorEnvelopeDto::class.java)?.error?.message ?: fallback
        } catch (ex: Exception) {
            fallback
        }
    }
}

/** Перетворення DTO -> доменна модель з перевіркою обов'язкових полів. */
object PlanMapper {
    fun map(dto: PlanResponseDto): PlanData {
        val c = dto.calories
        val meals = dto.meals
        if (c?.bmr == null || c.tdee == null || c.target == null || meals.isNullOrEmpty() || dto.totalKcal == null) {
            throw PlanException("Сервер повернув неповні дані. Спробуйте ще раз.")
        }
        return PlanData(
            bmr = c.bmr,
            tdee = c.tdee,
            target = c.target,
            meals = meals.map { m ->
                val items = m.items
                if (m.name == null || m.kcal == null || items.isNullOrEmpty()) {
                    throw PlanException("Сервер повернув неповні дані. Спробуйте ще раз.")
                }
                MealData(
                    name = m.name,
                    kcal = m.kcal,
                    items = items.map { i ->
                        if (i.name == null || i.grams == null || i.kcal == null) {
                            throw PlanException("Сервер повернув неповні дані. Спробуйте ще раз.")
                        }
                        MealItemData(i.name, i.grams, i.kcal)
                    },
                )
            },
            totalKcal = dto.totalKcal,
            deviationPct = dto.deviationPct ?: 0.0,
            aiSource = dto.source == "gemini",
            warnings = dto.warnings.orEmpty(),
            disclaimer = dto.disclaimer.orEmpty(),
        )
    }
}
