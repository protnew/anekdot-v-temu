package com.anekdot.vtemu.util

object CatEmojis {
    private val map = mapOf(
        "работа" to "💼",
        "айти" to "💻",
        "it" to "💻",
        "деньги" to "💰",
        "семья" to "👨‍👩‍👧",
        "политика" to "🏛️",
        "здоровье" to "🏥",
        "путешествия" to "✈️",
        "еда" to "🍽️",
        "наука" to "🔬",
        "спорт" to "⚽",
        "образование" to "🎓",
        "отношения" to "💑",
        "коронавирус" to "😷",
        "искусственный интеллект" to "🤖",
        "ai" to "🤖",
        "друзья" to "🤝",
        "котики" to "🐱",
        "кошки" to "🐱",
        "авто" to "🚗",
        "автомобили" to "🚗",
        "магазины" to "🛒",
        "дети" to "👶",
        "реклама" to "📢",
        "разное" to "📖"
    )

    fun get(cat: String?): String {
        if (cat == null) return "📖"
        val lower = cat.lowercase().trim()
        return map[lower] ?: "📖"
    }

    fun withLabel(cat: String?): String {
        val emoji = get(cat)
        return if (cat != null) "$emoji $cat" else "📖 Разное"
    }
}
