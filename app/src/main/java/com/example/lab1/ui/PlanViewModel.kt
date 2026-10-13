package com.example.lab1.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.lab1.data.NetworkPlanRepository
import com.example.lab1.data.PlanData
import com.example.lab1.data.PlanRepository
import com.example.lab1.data.PlanRequestDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Стан екрана: Idle -> Loading -> Success | Error. */
sealed class UiState {
    data object Idle : UiState()
    data object Loading : UiState()
    data class Success(val data: PlanData) : UiState()
    data class Error(val message: String) : UiState()
}

data class FormState(
    val age: String = "",
    val weight: String = "",
    val height: String = "",
    val sex: String = "female",
    val activity: String = "moderate",
    val goal: String = "maintain",
    val excluded: String = "",
    val errors: Map<String, String> = emptyMap(),
)

class PlanViewModel(
    private val repository: PlanRepository = NetworkPlanRepository(),
) : ViewModel() {

    private val _form = MutableStateFlow(FormState())
    val form: StateFlow<FormState> = _form.asStateFlow()

    private val _ui = MutableStateFlow<UiState>(UiState.Idle)
    val ui: StateFlow<UiState> = _ui.asStateFlow()

    fun onAge(v: String) = _form.update { it.copy(age = v.filter(Char::isDigit).take(3), errors = it.errors - "age") }
    fun onWeight(v: String) = _form.update { it.copy(weight = number(v), errors = it.errors - "weight") }
    fun onHeight(v: String) = _form.update { it.copy(height = number(v), errors = it.errors - "height") }
    fun onSex(v: String) = _form.update { it.copy(sex = v) }
    fun onActivity(v: String) = _form.update { it.copy(activity = v) }
    fun onGoal(v: String) = _form.update { it.copy(goal = v) }
    fun onExcluded(v: String) = _form.update { it.copy(excluded = v.take(200)) }

    private fun number(v: String): String = v.filter { it.isDigit() || it == '.' || it == ',' }.take(6)

    /** Валідація на клієнті: некоректні або порожні дані на сервер не надсилаємо. */
    fun validate(f: FormState): Pair<PlanRequestDto?, Map<String, String>> {
        val errors = mutableMapOf<String, String>()
        val age = f.age.toIntOrNull()
        val weight = f.weight.replace(',', '.').toDoubleOrNull()
        val height = f.height.replace(',', '.').toDoubleOrNull()
        if (age == null) errors["age"] = "Введіть вік" else if (age !in 16..60) errors["age"] = "Вік має бути 16-60"
        if (weight == null) errors["weight"] = "Введіть вагу" else if (weight < 30 || weight > 250) errors["weight"] = "Вага 30-250 кг"
        if (height == null) errors["height"] = "Введіть зріст" else if (height < 120 || height > 230) errors["height"] = "Зріст 120-230 см"
        val excluded = f.excluded.split(',', ';').map { it.trim() }.filter { it.isNotEmpty() }
        if (excluded.size > 10) errors["excluded"] = "Не більше 10 винятків"
        if (errors.isNotEmpty()) return null to errors
        return PlanRequestDto(age!!, f.sex, weight!!, height!!, f.activity, f.goal, excluded) to emptyMap()
    }

    fun submit() {
        if (_ui.value is UiState.Loading) return          // захист від подвійного натискання
        val (request, errors) = validate(_form.value)
        if (request == null) {
            _form.update { it.copy(errors = errors) }
            return
        }
        _ui.value = UiState.Loading
        viewModelScope.launch {
            repository.createPlan(request).fold(
                onSuccess = { _ui.value = UiState.Success(it) },
                onFailure = { _ui.value = UiState.Error(it.message ?: "Невідома помилка") },
            )
        }
    }

    /** Повторна відправка без перезапуску застосунку. */
    fun retry() = submit()
}
