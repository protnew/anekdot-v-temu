package com.anekdot.vtemu.api

sealed class ApiResponse<out T> {
    data class Success<T>(val data: T) : ApiResponse<T>()
    data class Error(val message: String, val code: Int = -1) : ApiResponse<Nothing>()

    val isSuccess: Boolean get() = this is Success
    val isError: Boolean get() = this is Error

    fun getOrNull(): T? = when (this) {
        is Success -> data
        is Error -> null
    }

    fun getOrDefault(default: T): T = when (this) {
        is Success -> data
        is Error -> default
    }

    fun getOrThrow(): T = when (this) {
        is Success -> data
        is Error -> throw IllegalStateException(message)
    }

    companion object {
        fun <T> success(data: T): ApiResponse<T> = Success(data)
        fun error(message: String, code: Int = -1): ApiResponse<Nothing> = Error(message, code)
    }
}
