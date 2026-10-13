package com.example.lab1.data

/**
 * Адреса backend.
 *  - Емулятор Android:      http://10.0.2.2:8000/   (10.0.2.2 = localhost комп'ютера)
 *  - Фізичний телефон:      http://<IP_комп'ютера_у_Wi-Fi>:8000/   (напр. http://192.168.0.15:8000/)
 */
object ApiConfig {
    const val BASE_URL = "http://10.0.2.2:8000/"
    const val TIMEOUT_SECONDS = 15L
}
