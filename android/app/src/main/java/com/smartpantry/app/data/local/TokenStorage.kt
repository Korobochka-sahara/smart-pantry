
package com.smartpantry.app.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

object TokenStorage {

    private const val PREFS_NAME = "secure_auth_prefs"
    private const val ACCESS_TOKEN_KEY = "access_token"
    private const val REFRESH_TOKEN_KEY = "refresh_token"

    private fun preferences(context: Context): SharedPreferences {
        val appContext = context.applicationContext

        val masterKey = MasterKey.Builder(appContext)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        return EncryptedSharedPreferences.create(
            appContext,
            PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    fun save(//Сохраняет оба токена после входа
        context: Context,
        accessToken: String,
        refreshToken: String
    ) {
        preferences(context).edit()
            .putString(ACCESS_TOKEN_KEY, accessToken)
            .putString(REFRESH_TOKEN_KEY, refreshToken)
            .apply()
    }

    fun getAccessToken(context: Context): String? {//Возвращает токен для запросов к API
        return preferences(context).getString(ACCESS_TOKEN_KEY, null)
    }

    fun getRefreshToken(context: Context): String? {//Возвращает токен для обновления сессии
        return preferences(context).getString(REFRESH_TOKEN_KEY, null)
    }

    fun clear(context: Context) {//Удаляет токены, например при выходе из аккаунта
        preferences(context).edit()
            .remove(ACCESS_TOKEN_KEY)
            .remove(REFRESH_TOKEN_KEY)
            .apply()
    }
}
