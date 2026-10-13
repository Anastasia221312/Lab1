package com.example.lab1.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.lab1.data.MealData
import com.example.lab1.data.MealItemData
import com.example.lab1.data.PlanData
import com.example.lab1.ui.theme.Lab1Theme

private val SEX = listOf("female" to "Жінка", "male" to "Чоловік")
private val ACTIVITY = listOf(
    "sedentary" to "Сидячий спосіб життя",
    "light" to "Легка активність (1-3 тренування/тиж.)",
    "moderate" to "Помірна (3-5 тренувань/тиж.)",
    "high" to "Висока (6-7 тренувань/тиж.)",
)
private val GOAL = listOf("lose" to "Схуднути", "maintain" to "Утримати вагу", "gain" to "Набрати")

/** Stateful-обгортка: бере стан з ViewModel. */
@Composable
fun PlanScreen(viewModel: PlanViewModel, modifier: Modifier = Modifier) {
    val form by viewModel.form.collectAsState()
    val ui by viewModel.ui.collectAsState()
    PlanContent(
        form = form, ui = ui, modifier = modifier,
        onAge = viewModel::onAge, onWeight = viewModel::onWeight, onHeight = viewModel::onHeight,
        onSex = viewModel::onSex, onActivity = viewModel::onActivity, onGoal = viewModel::onGoal,
        onExcluded = viewModel::onExcluded, onSubmit = viewModel::submit, onRetry = viewModel::retry,
    )
}

/** Stateless-екран (зручно для Preview та тестів). */
@Composable
fun PlanContent(
    form: FormState,
    ui: UiState,
    modifier: Modifier = Modifier,
    onAge: (String) -> Unit = {}, onWeight: (String) -> Unit = {}, onHeight: (String) -> Unit = {},
    onSex: (String) -> Unit = {}, onActivity: (String) -> Unit = {}, onGoal: (String) -> Unit = {},
    onExcluded: (String) -> Unit = {}, onSubmit: () -> Unit = {}, onRetry: () -> Unit = {},
) {
    Column(
        modifier = modifier.verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Дієтокс", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Text("Розрахунок норми калорій і AI-план харчування на день", style = MaterialTheme.typography.bodyMedium)

        NumberField("Вік (16-60)", form.age, form.errors["age"], onAge, KeyboardType.Number)
        NumberField("Вага, кг", form.weight, form.errors["weight"], onWeight, KeyboardType.Decimal)
        NumberField("Зріст, см", form.height, form.errors["height"], onHeight, KeyboardType.Decimal)

        Section("Стать"); Choices(SEX, form.sex, onSex)
        Section("Рівень активності"); Choices(ACTIVITY, form.activity, onActivity)
        Section("Ціль"); Choices(GOAL, form.goal, onGoal)

        OutlinedTextField(
            value = form.excluded, onValueChange = onExcluded, modifier = Modifier.fillMaxWidth(),
            label = { Text("Не вживаю (через кому): молоко, горіхи...") },
            isError = form.errors.containsKey("excluded"),
            supportingText = form.errors["excluded"]?.let { { Text(it) } },
        )

        Button(
            onClick = onSubmit, modifier = Modifier.fillMaxWidth(),
            enabled = ui !is UiState.Loading,
        ) { Text(if (ui is UiState.Success) "Створити інший план" else "Створити план") }

        when (ui) {
            UiState.Idle -> Unit
            UiState.Loading -> LoadingBlock()
            is UiState.Success -> PlanResult(ui.data)
            is UiState.Error -> ErrorBlock(ui.message, onRetry)
        }
    }
}

@Composable
private fun Section(title: String) =
    Text(title, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)

@Composable
private fun NumberField(label: String, value: String, error: String?, onChange: (String) -> Unit, type: KeyboardType) {
    OutlinedTextField(
        value = value, onValueChange = onChange, modifier = Modifier.fillMaxWidth(),
        label = { Text(label) }, singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = type),
        isError = error != null, supportingText = error?.let { { Text(it) } },
    )
}

@Composable
private fun Choices(options: List<Pair<String, String>>, selected: String, onSelect: (String) -> Unit) {
    Column {
        options.forEach { (key, label) ->
            Row(
                Modifier.fillMaxWidth().selectable(selected = key == selected, role = Role.RadioButton) { onSelect(key) },
                verticalAlignment = Alignment.CenterVertically,
            ) {
                RadioButton(selected = key == selected, onClick = null)
                Text(label, modifier = Modifier.padding(start = 8.dp, top = 6.dp, bottom = 6.dp))
            }
        }
    }
}

@Composable
private fun LoadingBlock() {
    Row(Modifier.fillMaxWidth().padding(vertical = 16.dp), horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
        CircularProgressIndicator(Modifier.size(28.dp))
        Text("  AI складає план...", modifier = Modifier.padding(start = 12.dp))
    }
}

@Composable
private fun ErrorBlock(message: String, onRetry: () -> Unit) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer), modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Помилка", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onErrorContainer)
            Text(message, color = MaterialTheme.colorScheme.onErrorContainer)
            OutlinedButton(onClick = onRetry) { Text("Спробувати ще раз") }
        }
    }
}

@Composable
private fun PlanResult(d: PlanData) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Ваша норма: ${d.target} ккал/день", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Text("Базовий обмін (BMR): ${d.bmr} ккал; з урахуванням активності (TDEE): ${d.tdee} ккал")
                Text(if (d.aiSource) "План склав AI (Gemini)" else "План складено базовим алгоритмом", style = MaterialTheme.typography.labelMedium)
            }
        }
        d.meals.forEach { meal ->
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text("${meal.name} — ${meal.kcal} ккал", fontWeight = FontWeight.SemiBold)
                    meal.items.forEach { Text("• ${it.name}: ${it.grams} г (${it.kcal} ккал)") }
                }
            }
        }
        Text("Разом: ${d.totalKcal} ккал (відхилення від норми ${d.deviationPct}%)", fontWeight = FontWeight.SemiBold)
        d.warnings.forEach { Text("⚠ $it", color = MaterialTheme.colorScheme.error) }
        if (d.disclaimer.isNotEmpty()) Text(d.disclaimer, style = MaterialTheme.typography.bodySmall)
        Spacer(Modifier.height(24.dp))
    }
}

// ---------------- Preview для кожного стану ----------------
private val previewData = PlanData(
    bmr = 1345, tdee = 2085, target = 2085,
    meals = listOf(
        MealData("Сніданок", listOf(MealItemData("Вівсяні пластівці (сухі)", 70, 256), MealItemData("Банан", 150, 134)), 520),
        MealData("Обід", listOf(MealItemData("Куряча грудка (варена)", 200, 330)), 730),
    ),
    totalKcal = 2073, deviationPct = 0.6, aiSource = false, warnings = emptyList(), disclaimer = "Застосунок не є медичним сервісом.",
)
private val previewForm = FormState(age = "25", weight = "60", height = "165")

@Preview(showBackground = true, name = "Idle") @Composable private fun PreviewIdle() = Lab1Theme { PlanContent(previewForm, UiState.Idle) }
@Preview(showBackground = true, name = "Loading") @Composable private fun PreviewLoading() = Lab1Theme { PlanContent(previewForm, UiState.Loading) }
@Preview(showBackground = true, name = "Success") @Composable private fun PreviewSuccess() = Lab1Theme { PlanContent(previewForm, UiState.Success(previewData)) }
@Preview(showBackground = true, name = "Error") @Composable private fun PreviewError() = Lab1Theme { PlanContent(previewForm, UiState.Error("Сервер недоступний. Перевірте з'єднання та спробуйте ще раз.")) }
