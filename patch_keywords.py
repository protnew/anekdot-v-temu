import sys
content = open('main.py', 'r', encoding='utf-8').read()
# Find insertion point: after the reklama keyword line
target = '"\u0440\u0435\u043a\u043b\u0430\u043c\u0430": ["\u0440\u0435\u043a\u043b\u0430\u043c"'
idx = content.find(target)
if idx == -1:
    print("MARKER NOT FOUND")
    sys.exit(1)
# Find end of the list for this entry
end = content.find('],', idx) + 2
extra = '\n    # Multilingual keywords\n'
langs = {
    "es_trabajo": ["trabajo", "jefe", "oficina", "empleado", "entrevista", "sueldo"],
    "de_arbeit": ["arbeit", "chef", "buro", "kollege", "gehalt", "meeting"],
    "fr_travail": ["travail", "patron", "bureau", "collegue", "salaire", "reunion"],
    "pt_trabalho": ["trabalho", "chefe", "escritorio", "entrevista", "salario"],
    "zh_misc": ["gongzuo", "laoban", "tongshi", "mianshi", "gongzi", "jiaban", "996"],
    "ja_work": ["shigoto", "joushi", "zangyou", "kyuuryou", "kaigi", "salaryman"],
    "ar_misc": ["amal", "mudir", "muwazzaf", "ratib", "ijtima"],
    "hi_work": ["kaam", "boss", "naukri", "salary", "office", "interview"],
}
for k, v in langs.items():
    extra += f'    "{k}": {v},\n'
content = content[:end] + extra + content[end:]
open('main.py', 'w', encoding='utf-8').write(content)
print("OK, multilingual keywords added")
