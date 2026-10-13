package com.example.lab1

import com.example.lab1.data.CaloriesDto
import com.example.lab1.data.MealDto
import com.example.lab1.data.MealItemDto
import com.example.lab1.data.PlanData
import com.example.lab1.data.PlanException
import com.example.lab1.data.PlanMapper
import com.example.lab1.data.PlanRepository
import com.example.lab1.data.PlanRequestDto
import com.example.lab1.data.PlanResponseDto
import com.example.lab1.ui.PlanViewModel
import com.example.lab1.ui.UiState
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test

private val okDto = PlanResponseDto(
    calories = CaloriesDto(1345, 2085, 2085),
    meals = listOf(MealDto("Сніданок", listOf(MealItemDto("Банан", 150, 134)), 134)),
    totalKcal = 134, deviationPct = 0.5, source = "rule-based", warnings = emptyList(), disclaimer = "x",
)

private class FakeRepo(var results: MutableList<Result<PlanData>>) : PlanRepository {
    var calls = 0
    val requests = mutableListOf<PlanRequestDto>()
    override suspend fun createPlan(request: PlanRequestDto): Result<PlanData> {
        calls++; requests += request
        return results.removeAt(0)
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
class PlanViewModelTest {
    @Before fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())
    @After fun tearDown() = Dispatchers.resetMain()

    private fun filled(vm: PlanViewModel) {
        vm.onAge("25"); vm.onWeight("60,5"); vm.onHeight("165"); vm.onExcluded("молоко, горіхи")
    }

    @Test fun emptyForm_doesNotCallBackend_andShowsFieldErrors() {
        val repo = FakeRepo(mutableListOf())
        val vm = PlanViewModel(repo)
        vm.submit()
        assertEquals(0, repo.calls)
        assertTrue(vm.ui.value is UiState.Idle)
        assertEquals(setOf("age", "weight", "height"), vm.form.value.errors.keys)
    }

    @Test fun outOfRangeAge_isRejectedOnClient() {
        val repo = FakeRepo(mutableListOf())
        val vm = PlanViewModel(repo)
        filled(vm); vm.onAge("70")
        vm.submit()
        assertEquals(0, repo.calls)
        assertNotNull(vm.form.value.errors["age"])
    }

    @Test fun happyPath_sendsParsedRequest_andShowsSuccess() {
        val repo = FakeRepo(mutableListOf(Result.success(PlanMapper.map(okDto))))
        val vm = PlanViewModel(repo)
        filled(vm); vm.submit()
        assertTrue(vm.ui.value is UiState.Success)
        val req = repo.requests.single()
        assertEquals(60.5, req.weightKg, 0.0)
        assertEquals(listOf("молоко", "горіхи"), req.excluded)
    }

    @Test fun error_thenRetry_succeedsWithoutRestart() {
        val repo = FakeRepo(mutableListOf(
            Result.failure(PlanException("Сервер недоступний")),
            Result.success(PlanMapper.map(okDto)),
        ))
        val vm = PlanViewModel(repo)
        filled(vm); vm.submit()
        assertEquals(UiState.Error("Сервер недоступний"), vm.ui.value)
        vm.retry()
        assertTrue(vm.ui.value is UiState.Success)
        assertEquals(2, repo.calls)
    }

    @Test fun mapper_rejectsBrokenResponse() {
        try {
            PlanMapper.map(okDto.copy(meals = null))
            fail("expected PlanException")
        } catch (e: PlanException) {
            assertTrue(e.message!!.contains("неповні"))
        }
    }
}
