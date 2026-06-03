#!/usr/bin/env python3
"""Add multilingual jokes: ES, DE, FR, PT, ZH, JA, AR, HI"""
import json, os, random, time

JOKES_DB = "data/jokes_db.json"

with open(JOKES_DB, "r", encoding="utf-8") as f:
    db = json.load(f)

new_jokes = {
    # ==================== SPANISH ====================
    "es_trabajo": [
        {"id": 30001, "text": "¿Por qué los programadores prefieren el modo oscuro? Porque la luz atrae los bugs.", "rating": 4.5, "tags": ["programación", "oscuridad"]},
        {"id": 30002, "text": "Mi jefe me dijo: '¡Tienes que tener iniciativa!' Así que me fui a casa temprano.", "rating": 4.3, "tags": ["jefe", "trabajo"]},
        {"id": 30003, "text": "¿Cuál es el colmo de un electricista? Que su mujer se llame Luz y sus hijos le sigan la corriente.", "rating": 4.6, "tags": ["profesiones", "juegos de palabras"]},
        {"id": 30004, "text": "En la entrevista de trabajo:\n— ¿Nivel de inglés?\n— Alto.\n— Traduzca 'mirar'.\n— Look.\n— Úselo en una frase.\n— Luke, yo soy tu padre.\n— Contratado.", "rating": 4.7, "tags": ["entrevista", "inglés", "star wars"]},
        {"id": 30005, "text": "— ¿Cómo se llama el hermano de Bruce Lee?\n— Broke Lee, porque siempre está sin dinero.", "rating": 4.2, "tags": ["humor", "nombres"]},
        {"id": 30006, "text": "¿Qué le dice un semáforo a otro? No me mires, me estoy cambiando.", "rating": 4.4, "tags": ["objetos", "cambio"]},
        {"id": 30007, "text": "Un hombre entra a una biblioteca y dice:\n— ¡Quiero una hamburguesa con patatas fritas!\n— Señor, esto es una biblioteca.\n— *susurrando* quiero una hamburguesa con patatas fritas.", "rating": 4.5, "tags": ["biblioteca", "clásico"]},
        {"id": 30008, "text": "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.", "rating": 4.3, "tags": ["tecnología", "redes sociales"]},
        {"id": 30009, "text": "Doctor, vengo a que me revise porque cada vez que tomo café no puedo dormir.\n— Eso es normal, señor.\n— ¿Normal? ¡Le echo azúcar, leche y todo!", "rating": 4.4, "tags": ["doctor", "café"]},
        {"id": 30010, "text": "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!", "rating": 4.1, "tags": ["animales", "gimnasio"]},
        {"id": 30011, "text": "¿Cuál es el animal más antiguo? La cebra, porque está en blanco y negro.", "rating": 4.0, "tags": ["animales", "clásico"]},
        {"id": 30012, "text": "Le digo a mi jefe: 'Jefe, ¿puedo salir temprano hoy? Mi esposa quiere que vaya de compras.'\n— Ni hablar.\n— Gracias jefe, sabía que podía contar con usted.", "rating": 4.5, "tags": ["jefe", "esposa"]},
        {"id": 30013, "text": "¿Por qué el libro de matemáticas estaba triste? Porque tenía muchos problemas.", "rating": 4.2, "tags": ["matemáticas", "escuela"]},
        {"id": 30014, "text": "Papá, ¿qué se siente tener un hijo tan guapo?\n— No sé hijo, pregúntale a tu abuelo.", "rating": 4.6, "tags": ["familia", "papá"]},
        {"id": 30015, "text": "¿Cuál es el país más resbaloso? Iran (I ran).", "rating": 3.8, "tags": ["geografía", "juegos de palabras"]},
        {"id": 30016, "text": "¿Qué le dice una pared a otra pared? Nos vemos en la esquina.", "rating": 4.3, "tags": ["objetos", "clásico"]},
        {"id": 30017, "text": "Me despidieron del trabajo en el banco. Una señora me preguntó si podía checar su balance... así que la empujé.", "rating": 4.4, "tags": ["banco", "inglés"]},
        {"id": 30018, "text": "¿Cuál es el colmo de un panadero? Que su hijo sea un buen pan para nada.", "rating": 4.1, "tags": ["profesiones", "pan"]},
        {"id": 30019, "text": "Ayer compré zapatos de un traficante. No sé con qué los cortó, pero estuve viajando todo el día.", "rating": 4.3, "tags": ["zapatos", "viaje"]},
        {"id": 30020, "text": "¿Qué le dijo el número 0 al número 8? ¡Bonito cinturón!", "rating": 4.0, "tags": ["números", "visual"]},
        {"id": 30021, "text": "¿Por qué Stewie de Family Guy no juega al escondite? Porque siempre lo encuentran (family guy).", "rating": 3.9, "tags": ["tv", "familia"]},
        {"id": 30022, "text": "¿Cómo se despiden los químicos? Ácido un placer.", "rating": 4.5, "tags": ["química", "juegos de palabras"]},
        {"id": 30023, "text": "Un taxi le dice a otro taxi: ¿Qué tal tu día? Y el otro le responde: ¡Eh, no me toques la carrera!", "rating": 4.2, "tags": ["taxi", "profesiones"]},
        {"id": 30024, "text": "Mi mujer me dijo: 'Elige, yo o el fútbol.' La voy a extrañar mucho.", "rating": 4.6, "tags": ["fútbol", "matrimonio"]},
        {"id": 30025, "text": "¿Qué tiene un pato que está patas arriba? Una mala postura.", "rating": 4.0, "tags": ["animales", "absurdo"]},
        {"id": 30026, "text": "¿Cuál es el colmo de un carnicero? Que su esposa se llame Salchicha y sus hijos le sigan el corte.", "rating": 4.3, "tags": ["profesiones", "colmo"]},
        {"id": 30027, "text": "Fui a una pelea de boxeo y de repente empezó un partido de ajedrez.", "rating": 3.9, "tags": ["deportes", "absurdo"]},
        {"id": 30028, "text": "¿Por qué las focas del circo miran siempre hacia arriba? Porque ahí están los focos.", "rating": 4.1, "tags": ["animales", "circo"]},
        {"id": 30029, "text": "Si un perezoso se tarda dos días en hacer algo, ¿cuánto se tarda medio perezoso? Un día.", "rating": 4.0, "tags": ["matemáticas", "perezoso"]},
        {"id": 30030, "text": "Me han dicho que soy egocéntrico. Pero basta de hablar de mí, hablemos de lo mucho que les agrado.", "rating": 4.4, "tags": ["ego", "humor"]},
    ],

    # ==================== GERMAN ====================
    "esson_sonstiges": [  # will rename below
    ],

    "de_arbeit": [
        {"id": 31001, "text": "Warum gehen Programmierers so gerne in den Dunkelmodus? Weil Licht Bugs anzieht.", "rating": 4.5, "tags": ["programmierung", "dunkel"]},
        {"id": 31002, "text": "Chef: 'Sie müssen mehr Eigeninitiative zeigen!' — Ich ging nach Hause.", "rating": 4.3, "tags": ["chef", "arbeit"]},
        {"id": 31003, "text": "Was ist der Höhepunkt eines Elektrikers? Seine Frau heißt Steffi (Strom) und die Kinder folgen ihm.", "rating": 4.2, "tags": ["beruf", "wortspiel"]},
        {"id": 31004, "text": "Treffen sich zwei Planeten. Sagt der eine: 'Mir geht's gar nicht gut, ich habe Homo sapiens.' Sagt der andere: 'Keine Sorge, das geht vorbei.'", "rating": 4.7, "tags": ["planeten", "menschen"]},
        {"id": 31005, "text": "Was sitzt auf dem Baum und winkt? Ein Huhu!", "rating": 3.8, "tags": ["tiere", "wortspiel"]},
        {"id": 31006, "text": "Warum können Geister so schlecht lügen? Weil man durch sie hindurchsehen kann.", "rating": 4.1, "tags": ["geister", "halloween"]},
        {"id": 31007, "text": "Egal wie gut du schläfst, Albert schläft wie Einstein.", "rating": 4.0, "tags": ["schlafen", "wissenschaft"]},
        {"id": 31008, "text": "Was ist orange und geht über den Berg? Eine Wanderine.", "rating": 4.3, "tags": ["obst", "wandern"]},
        {"id": 31009, "text": "Sagt der Optiker: 'Sie brauchen eine Brille.' — 'Wie kommen Sie denn darauf?' — 'Na, das ist hier ein Bank.", "rating": 4.4, "tags": ["optiker", "brille"]},
        {"id": 31010, "text": "Was macht ein Clown im Büro? Faxen.", "rating": 4.1, "tags": ["clown", "büro"]},
        {"id": 31011, "text": "Mein Chef hat gesagt ich soll Selbstbewusster auftreten. Ab morgen komme ich im Badeanzug.", "rating": 4.5, "tags": ["chef", "selbstbewusst"]},
        {"id": 31012, "text": "Treffen sich zwei Magnete. Sagt der eine: 'Was soll ich anziehen?'", "rating": 4.2, "tags": ["physik", "anzug"]},
        {"id": 31013, "text": "Frau: 'Schatz, was denkst du?' Mann: 'Das gleiche wie du.' Frau: 'DANN WIRST DU AUCH GESTRÄFNT!'", "rating": 4.6, "tags": ["ehe", "denken"]},
        {"id": 31014, "text": "Was bestellt ein Maulwurf im Restaurant? Ein Menü mit drei Gängen.", "rating": 4.0, "tags": ["tiere", "restaurant"]},
        {"id": 31015, "text": "Arzt: 'Ich habe eine gute und eine schlechte Nachricht.' Patient: 'Die gute zuerst!' Arzt: 'Sie haben 24 Stunden zu leben.' Patient: 'Und die schlechte?!' Arzt: 'Ich habe gestern vergessen Sie anzurufen.'", "rating": 4.5, "tags": ["arzt", "schwarz"]},
        {"id": 31016, "text": "Warum trinken Programmierer immer Tee? Weil in Java kein Kaffee ist, nur Kaffee-Bohnen.", "rating": 4.2, "tags": ["java", "programmierung"]},
        {"id": 31017, "text": "Was ist ein Keks unter einem Baum? Ein schattiges Plätzchen.", "rating": 4.3, "tags": ["keks", "wortspiel"]},
        {"id": 31018, "text": "Lehrer: 'Nenne mir drei Tiere aus Afrika.' Schüler: 'Ein Löwe und zwei Giraffen.'", "rating": 4.1, "tags": ["schule", "tiere"]},
        {"id": 31019, "text": "Was sagt ein Esel wenn er rückwärts geht? 'Iaaaah, rückwärts geht!'", "rating": 3.9, "tags": ["tiere", "absurd"]},
        {"id": 31020, "text": "Ein Fisch im Aquarium sagt: 'Mann, wie regiere ich dieses Land?'", "rating": 4.4, "tags": ["fisch", "politik"]},
        {"id": 31021, "text": "Was macht ein Pirat am Computer? Er drückt die Enter-Taste.", "rating": 4.0, "tags": ["pirat", "computer"]},
        {"id": 31022, "text": "Kommt ein Mann in die Bäckerei: 'Ich hätte gerne ein Brot.' Bäcker: 'Gerne, haben sie es gesehen?'", "rating": 4.3, "tags": ["bäcker", "wortspiel"]},
        {"id": 31023, "text": "Standup-Comedy in Deutschland: 'Guten Abend!' *Publikum notiert: zu informell.*", "rating": 4.6, "tags": ["deutschland", "kultur"]},
        {"id": 31024, "text": "Eheberatung: 'Sie müssen mehr kommunizieren!' Er: 'Okay.' Sie: 'Okay.' *Stille für 45 Minuten.*", "rating": 4.5, "tags": ["ehe", "deutsch"]},
        {"id": 31025, "text": "Deutsche Grammatik: Lass Adjektive weg und du klingst wie ein Bundesliga-Trainer nach dem Spiel.", "rating": 4.4, "tags": ["grammatik", "fussball"]},
    ],

    "de_sonstiges": [],  # placeholder - all in de_arbeit

    # ==================== FRENCH ====================
    "fr_travail": [
        {"id": 32001, "text": "Pourquoi les plongeurs plongent-ils toujours en arrière et jamais en avant ? Parce que sinon ils tomberaient dans le bateau.", "rating": 4.6, "tags": ["plongée", "logique"]},
        {"id": 32002, "text": "Qu'est-ce qu'un crocodile qui surveille la cour de récréation ? Un surveillant.", "rating": 4.3, "tags": ["école", "jeu de mots"]},
        {"id": 32003, "text": "Quel est le comble pour un électricien ? De ne pas être au courant.", "rating": 4.5, "tags": ["électricien", "jeu de mots"]},
        {"id": 32004, "text": "Un homme demande à son chef : 'Est-ce que je peux partir tôt aujourd'hui ?' Le chef : 'Oui, à quelle heure rentrez-vous demain ?'", "rating": 4.4, "tags": ["travail", "chef"]},
        {"id": 32005, "text": "Pourquoi les Belges ne mangent-ils pas de smarties ? Parce qu'ils ont du mal à enlever les caissettes.", "rating": 4.0, "tags": ["belge", "candy"]},
        {"id": 32006, "text": "C'est l'histoire d'un pingouin qui respire par les fesses. Un jour il s'assoit et il meurt.", "rating": 4.2, "tags": ["animaux", "noir"]},
        {"id": 32007, "text": "Qu'est-ce qu'un canif ? Un petit fien.", "rating": 3.9, "tags": ["jeu de mots", " classique"]},
        {"id": 32008, "text": "Toto à la maîtresse : 'Est-ce qu'on est puni pour quelque chose qu'on n'a pas fait ?' La maîtresse : 'Non bien sûr.' Toto : 'Ah bon, parce que je n'ai pas fait mon devoir.'", "rating": 4.5, "tags": ["école", "toto"]},
        {"id": 32009, "text": "Pourquoi le chat est-il allé à l'ordinateur ? Pour surveiller la souris.", "rating": 4.1, "tags": ["chat", "ordinateur"]},
        {"id": 32010, "text": "Le pharmacien : 'Voilà, c'est 15 euros.' Le client : 'Mais c'est écrit 10 sur l'étiquette !' Le pharmacien : 'Oui, mais l'étiquette est en supplément.'", "rating": 4.3, "tags": ["pharmacie", "commerce"]},
        {"id": 32011, "text": "Quel est le comble pour un avion ? D'avoir un antivol.", "rating": 4.2, "tags": ["avion", "jeu de mots"]},
        {"id": 32012, "text": "Un chat tombe dans l'eau. Que dit-il ? 'Miaou.' Qu'est-ce que vous vouliez qu'il dise ?", "rating": 3.8, "tags": ["chat", "absurde"]},
        {"id": 32013, "text": "C'est un gars qui va chez le médecin. 'Docteur, tout le monde m'ignore.' Le médecin : 'Suivant !'", "rating": 4.6, "tags": ["médecin", "social"]},
        {"id": 32014, "text": "Pourquoi les Français mangent-ils des escargots ? Parce qu'ils n'aiment pas la fast food.", "rating": 4.3, "tags": ["français", "nourriture"]},
        {"id": 32015, "text": "La femme : 'Chéri, dis-moi quelque chose de doux.' Lui : 'Sucre.' Elle : 'Non, quelque chose de romantique !' Lui : 'Sucre candi.'", "rating": 4.1, "tags": ["couple", "romantique"]},
        {"id": 32016, "text": "Comment appelle-t-on un chien sans pattes ? On ne l'appelle pas, on va le chercher.", "rating": 4.4, "tags": ["chien", "noir"]},
        {"id": 32017, "text": "Pourquoi les plombiers sont-ils toujours calmes ? Parce qu'ils savent que tout coule de source.", "rating": 4.0, "tags": ["plombier", "calme"]},
        {"id": 32018, "text": "Un policier arrête un conducteur : 'Papier !' Le conducteur : 'Ciseaux ! J'ai gagné !'", "rating": 4.5, "tags": ["police", "jeu"]},
        {"id": 32019, "text": "Qu'est-ce qu'un cheese qui court ? Un fromage qui pue.", "rating": 3.7, "tags": ["fromage", "jeu de mots"]},
        {"id": 32020, "text": "Mon médecin m'a dit de manger plus de fibres. Alors je mange du papier.", "rating": 4.0, "tags": ["médecin", "absurde"]},
        {"id": 32021, "text": "Pourquoi la Tour Eiffel ne fait-elle jamais de bruit ? Parce qu'elle a des antennes.", "rating": 3.9, "tags": ["paris", "tour eiffel"]},
        {"id": 32022, "text": "Je suis allé au restaurant et j'ai demandé un croque-monsieur. Le serveur m'a répondu : 'Non, je suis célibataire.'", "rating": 4.3, "tags": ["restaurant", "jeu de mots"]},
        {"id": 32023, "text": "Que fait une fraise sur un cheval ? Tagada tagada !", "rating": 4.2, "tags": ["fraise", "bonbon"]},
        {"id": 32024, "text": "C'est la rentrée. La maîtresse demande à Toto : 'Où est ton cahier ?' Toto : 'Il est pas cahier, il est devenu canard.'", "rating": 4.0, "tags": ["école", "toto"]},
        {"id": 32025, "text": "La grève est un droit français. Ne pas travailler aussi. Les deux combinés, c'est la fonction publique.", "rating": 4.5, "tags": ["grève", "administration"]},
    ],

    # ==================== PORTUGUESE ====================
    "pt_trabalho": [
        {"id": 33001, "text": "Por que o livro de matemática ficou triste? Porque tinha muitos problemas.", "rating": 4.3, "tags": ["matemática", "escola"]},
        {"id": 33002, "text": "O que o pato disse para a pata? Vem Quá!", "rating": 3.9, "tags": ["animais", "trocadilho"]},
        {"id": 33003, "text": "Por que o computador foi ao médico? Porque pegou um vírus.", "rating": 4.2, "tags": ["computador", "médico"]},
        {"id": 33004, "text": "Chefe: 'Você chegou atrasado de novo!' Funcionário: 'Desculpa, o ônibus atrasou.' Chefe: 'Mas eu vi você descendo do ônibus!' Funcionário: 'É, o ônibus atrasou minha descida também.'", "rating": 4.4, "tags": ["trabalho", "atraso"]},
        {"id": 33005, "text": "O que uma impressora disse para a outra? Essa folha é sua ou é impressão minha?", "rating": 4.6, "tags": ["tecnologia", "trocadilho"]},
        {"id": 33006, "text": "Joãozinho: 'Professora, posso ser punido por algo que não fiz?' Professora: 'Claro que não!' Joãozinho: 'Ótimo, porque não fiz a lição!'", "rating": 4.5, "tags": ["escola", "joãozinho"]},
        {"id": 33007, "text": "Por que o mergulhador entra de costas na água? Porque se entrasse de frente cairia no barco.", "rating": 4.3, "tags": ["mergulho", "lógica"]},
        {"id": 33008, "text": "Qual é o cúmulo da tecnologia? Um cara usando um iPhone com capa de Nokia 3310.", "rating": 4.1, "tags": ["tecnologia", "celular"]},
        {"id": 33009, "text": "O que o zero disse para o oito? Bonito cinto!", "rating": 4.0, "tags": ["números", "visual"]},
        {"id": 33010, "text": "No casamento: 'Você promete amar, honrar e obedecer?' A noiva: 'Eu prometo amar e honrar... o obedeço a gente vê depois.'", "rating": 4.4, "tags": ["casamento", "humor"]},
        {"id": 33011, "text": "Um cara entra no bar e pede um café. O garçom: 'Aqui não servimos café.' O cara: 'Traz uma cerveja então, pra eu não perder a viagem.'", "rating": 4.2, "tags": ["bar", "brasileiro"]},
        {"id": 33012, "text": "O que a mamma disse pro filho na escola? 'Estuda pra não ser burro como seu pai!' O filho: 'Mas mãe, o pai é rico!' Mãe: 'Pois é, imagina se fosse inteligente!'", "rating": 4.5, "tags": ["família", "escola"]},
        {"id": 33013, "text": "Mulher para o marido: 'Amor, você me ama mais do que ontem?' Marido: 'Claro, ontem eu com aquele feijão que você fez.'", "rating": 4.3, "tags": ["casamento", "comida"]},
        {"id": 33014, "text": "Por que o Jacaré tirou o jacaré? Porque ele queria ficar só com o Ré.", "rating": 3.8, "tags": ["animais", "trocadilho"]},
        {"id": 33015, "text": "O brasileiro quando ganha na loteria: primeira coisa que faz? Compra um chinelo novo de marca.", "rating": 4.4, "tags": ["brasileiro", "estereótipo"]},
        {"id": 33016, "text": "O que o café disse para o açúcar? 'Sem você minha vida é amarga.'", "rating": 4.1, "tags": ["café", "romântico"]},
        {"id": 33017, "text": "Você sabe como se chama o cara que perdeu 50% do cérebro? Hemiplégico... não, brasileiro médio.", "rating": 4.0, "tags": ["brasileiro", "irônico"]},
        {"id": 33018, "text": "Chega a seleção brasileira no céu. São Pedro: 'Aqui não, vocês já perderam 7x1 na terra.'", "rating": 4.5, "tags": ["futebol", "7x1"]},
        {"id": 33019, "text": "Qual é a cidade brasileira que não pode faltar no churrasco? Guarulhos (Gua-rulhos = garrafa de rhos).", "rating": 3.9, "tags": ["cidades", "churrasco"]},
        {"id": 33020, "text": "No Brasil, se você disser 'vou ali e volto já', pode preparar o café porque a pessoa vai demorar.", "rating": 4.3, "tags": ["brasileiro", "costumes"]},
    ],

    # ==================== CHINESE ====================
    "zh_各种": [
        {"id": 34001, "text": "老师问小明：用也许造句。小明：也许三升水吧。", "rating": 4.2, "tags": ["学校", "谐音"]},
        {"id": 34002, "text": "一只北极熊在发呆，突然觉得自己好冷。", "rating": 4.0, "tags": ["动物", "冷笑话"]},
        {"id": 34003, "text": "问：为什么程序员总是分不清万圣节和圣诞节？答：因为 Oct 31 = Dec 25。", "rating": 4.5, "tags": ["程序员", "节日"]},
        {"id": 34004, "text": "我跟我爸说：'爸，我想当工程师。' 我爸说：'不行，你必须先学会拧螺丝。'", "rating": 4.1, "tags": ["职业", "父子"]},
        {"id": 34005, "text": "从前有个人叫小明，后来他长大了，就不叫小明了，叫大明。", "rating": 3.8, "tags": ["小明", "无聊"]},
        {"id": 34006, "text": "为什么数学书总是很忧伤？因为它有太多问题了（problems）。", "rating": 4.2, "tags": ["数学", "翻译"]},
        {"id": 34007, "text": "老婆：你看隔壁老王多浪漫！老公：那你去找他啊！老婆：我已经去了。", "rating": 4.4, "tags": ["婚姻", "反转"]},
        {"id": 34008, "text": "面试官：你最大的优点是什么？我：我特别执着。面试官：举个例子。我：你什么时候录用我？", "rating": 4.5, "tags": ["面试", "执着"]},
        {"id": 34009, "text": "老板说：把公司当家一样。于是我躺在沙发上玩手机。", "rating": 4.6, "tags": ["老板", "公司"]},
        {"id": 34010, "text": "问：世界上最短的笑话是什么？答：努力工作就能致富。", "rating": 4.5, "tags": ["工作", "讽刺"]},
        {"id": 34011, "text": "医生：'你的病很严重。' 病人：'那我去找第二意见。' 医生：'好的，你也很丑。'", "rating": 4.3, "tags": ["医生", "反转"]},
        {"id": 34012, "text": "我去饭店吃饭，跟服务员说：来碗面。服务员说：要什么面？我说：见面。", "rating": 4.1, "tags": ["饭店", "谐音"]},
        {"id": 34013, "text": "一个人去看电影，买了一张票。进去一看，全满座。他拍了一下自己的脑袋：'我应该买两张的！'", "rating": 3.9, "tags": ["电影", "冷笑话"]},
        {"id": 34014, "text": "问：为什么飞机飞这么高？答：因为地下有房贷。", "rating": 4.4, "tags": ["房子", "现代"]},
        {"id": 34015, "text": "我妈问我：你怎么又在玩手机？我说：我没有在玩手机，手机在玩我。", "rating": 4.2, "tags": ["手机", "现代"]},
        {"id": 34016, "text": "同事问我：你中午吃什么？我说：吃亏。同事说：那够饱的。", "rating": 4.0, "tags": ["同事", "谐音"]},
        {"id": 34017, "text": "996工作制：早9点到晚9点，一周6天。这哪是工作，这是修仙。", "rating": 4.6, "tags": ["996", "程序员"]},
        {"id": 34018, "text": "我对女朋友说：我愿意为你上九天揽月，下五洋捉鳖。她说：那你先把碗洗了。", "rating": 4.5, "tags": ["恋爱", "现实"]},
        {"id": 34019, "text": "问：怎样才能让一本书畅销？答：在封面上写'减肥秘诀'。", "rating": 4.3, "tags": ["减肥", "营销"]},
        {"id": 34020, "text": "从前有个馒头，走着走着饿了，就把自己吃了。", "rating": 4.0, "tags": ["食物", "冷笑话"]},
    ],

    # ==================== JAPANESE ====================
    "ja_仕事": [
        {"id": 35001, "text": "上司「もっと主体性を持って！」→ 帰宅した。", "rating": 4.3, "tags": ["上司", "仕事"]},
        {"id": 35002, "text": "なぜプログラマーはダークモードが好きなのか？光はバグを引き寄せるから。", "rating": 4.5, "tags": ["プログラマー", "PC"]},
        {"id": 35003, "text": "先生「志望動機は？」学生「家から近いからです。」先生「正直ですね。」学生「はい、それが私の長所です。」", "rating": 4.4, "tags": ["面接", "正直"]},
        {"id": 35004, "text": "電気店で店員に「Wi-Fiのパスワードを教えてください」と言ったら「お客様自身で設定してください」と言われた。", "rating": 4.1, "tags": ["WiFi", "店"]},
        {"id": 35005, "text": "嫁「ねえ、聞いてる？」俺「うん。」嫁「じゃあ今何て言った？」俺「…。」", "rating": 4.6, "tags": ["夫婦", "共感"]},
        {"id": 35006, "text": "カレーと私の違い？カレーは温かい。", "rating": 4.0, "tags": ["自虐", "カレー"]},
        {"id": 35007, "text": "残業が終わった時の帰り道、風が気持ちいい。それが唯一のボーナス。", "rating": 4.5, "tags": ["残業", "サラリーマン"]},
        {"id": 35008, "text": "「残業しますか？」「いいえ、残業が私をします。」", "rating": 4.4, "tags": ["残業", "名言"]},
        {"id": 35009, "text": "ダイエットのためにジムに入会した。お金が減っただけだった。", "rating": 4.2, "tags": ["ダイエット", "ジム"]},
        {"id": 35010, "text": "医者「運動してください。」私「Wii Sportsでいいですか？」医者「…まあ。」", "rating": 4.1, "tags": ["医者", "運動"]},
        {"id": 35011, "text": "満員電車で「すみません」と言ったら、全員が謝ってきた。これが日本だ。", "rating": 4.6, "tags": ["電車", "日本"]},
        {"id": 35012, "text": "コンビニで「温めますか？」と聞かれて、心が温まりました。", "rating": 4.3, "tags": ["コンビニ", "温かい"]},
        {"id": 35013, "text": "日本の四季：春（花粉）、夏（暑い）、秋（台風）、冬（寒い）。素晴らしい。", "rating": 4.5, "tags": ["四季", "日本"]},
        {"id": 35014, "text": "経理に「交通費の領収書は？」と聞かれて、人生の領収書を出したくなった。", "rating": 4.2, "tags": ["経理", "人生"]},
        {"id": 35015, "text": "ネコに「可愛い」と言ったら、当たり前だという顔をされた。", "rating": 4.3, "tags": ["猫", "あるある"]},
        {"id": 35016, "text": "AIが私の仕事を奪うって？じゃあ私の残業も奪ってくれ。", "rating": 4.7, "tags": ["AI", "残業"]},
        {"id": 35017, "text": "「仕事は何？」→「IT系」→「パソコン直して」→（もうやめた）", "rating": 4.5, "tags": ["IT", "あるある"]},
        {"id": 35018, "text": "給料日が来た。そしてすぐに去っていった。風のように。", "rating": 4.4, "tags": ["給料", "切ない"]},
        {"id": 35019, "text": "朝起きるのが一番つらい運動だ。", "rating": 4.1, "tags": ["朝", "運動"]},
        {"id": 35020, "text": "田中さんはいつも定時で帰る。みんなは「すごい」と思っている。田中さんは「限界だから帰る」のだ。", "rating": 4.6, "tags": ["定時", "サラリーマン"]},
    ],

    # ==================== ARABIC ====================
    "ar_متنوعة": [
        {"id": 36001, "text": "واحد سأل صاحبه: ليش البحر أزرق؟ قال: لأنه شاف السمك وقال: بلو بلو بلو.", "rating": 4.2, "tags": ["بحر", "نكتة"]},
        {"id": 36002, "text": "مدرس: اكتب جملة فيها كلمة 'حليب'. الطالب: البقرة تعطينا حليب. المدرس: ممتاز! الطالب بس ما شربت.", "rating": 4.0, "tags": ["مدرسة", "طالب"]},
        {"id": 36003, "text": "واحد قال لصاحبه: عندي وظيفة بسيطة لك. قال: شو هي؟ قال: اضحك معي عشان الناس يظنوا إنا فاهمين.", "rating": 4.3, "tags": ["عمل", "ضحك"]},
        {"id": 36004, "text": "ليش الكمبيوتر راح للدكتور؟ لأن عنده فيروس!", "rating": 4.1, "tags": ["كمبيوتر", "طبيب"]},
        {"id": 36005, "text": "سألوا واحد كسول: ليش ما تشتغل؟ قال: أنا مش عاطل، أنا مستريح من المستقبل.", "rating": 4.4, "tags": ["كسل", "عمل"]},
        {"id": 36006, "text": "مدير: لازم تكون أكثر التزاماً! الموظف: أوكي، من بكرا بجي متأخر بانتظام.", "rating": 4.5, "tags": ["مدير", "موظف"]},
        {"id": 36007, "text": "واحد غني قال للفقير: الفلوس ما تجيب السعادة. الفقير: طيب خلّيها عندي أنا أبطلعلك.", "rating": 4.6, "tags": ["فلوس", "غني"]},
        {"id": 36008, "text": "الدكتور: لازم تقلل أكل. المريض: دكتور، أنا بأكل مرة باليوم. الدكتور: وهذا أكيد الظهر!", "rating": 4.2, "tags": ["دكتور", "أكل"]},
        {"id": 36009, "text": "واحد دخل السوبرماركت وطلب رقم صاحبه. البائع: هنا منتجات مش خدمات!", "rating": 4.0, "tags": ["سوبرماركت", "غبي"]},
        {"id": 36010, "text": "الزوجة: شو تحب أكثر، أنا ولا التلفزيون؟ الزوج: التلفزيون ما بيسأل أسئلة.", "rating": 4.5, "tags": ["زواج", "تلفزيون"]},
        {"id": 36011, "text": "في امتحان الرياضيات: سؤال: إذا كان عندك 10 تفاحات وأكلت 5، كم باقي؟ الطالب: بطن يؤلمني.", "rating": 4.3, "tags": ["مدرسة", "رياضيات"]},
        {"id": 36012, "text": "واحد سافر 40 سنة ويرجع يلاقي بيته نفسه. سأل جاره: ليش ما تغير شيء؟ الجار: لأنك ما شلتني معك.", "rating": 4.1, "tags": ["سفر", "جار"]},
        {"id": 36013, "text": "البناء: أنا أبني المستقبل. النجار: أنا أعمل الأثاث. الكهربائي: وأنا بأخليهم يشوفوا شغلهم.", "rating": 4.4, "tags": ["مهنة", "كهرباء"]},
        {"id": 36014, "text": "ليش النملة ما تروح السينما؟ لأن الفيلم ما بيكون بثواني.", "rating": 3.9, "tags": ["حشرات", "سينما"]},
        {"id": 36015, "text": "أبو الشباب: ليش راسب؟ الابن: لأن الأسئلة صعبة. الأبو: والثاني ليش ناجح؟ الابن: لأن الأسئلة كانت أسهل عندو.", "rating": 4.2, "tags": ["مدرسة", "أب"]},
        {"id": 36016, "text": "صاحبي قال: أنا صايم عن الأكل. قلت: إنت صايم عن الشغل من زمان!", "rating": 4.3, "tags": ["صيام", "عمل"]},
        {"id": 36017, "text": "سألوا حكيم: شو سر الزواج السعيد؟ قال: الزوج يسكت والزوجة تسمع... وكل واحد يعكس.", "rating": 4.5, "tags": ["زواج", "حكمة"]},
        {"id": 36018, "text": "أنا مش كسول، أنا بوطنية عالية — بقلل البطالة بشغل واحد أقل.", "rating": 4.4, "tags": ["عمل", "وطنية"]},
        {"id": 36019, "text": "حكمة: لو الشغل صح، ليش بيطلعوا لنا إجازة نرتاح منه؟", "rating": 4.3, "tags": ["عمل", "حكمة"]},
        {"id": 36020, "text": "في اجتماع: المدير: عندنا أخبار جيدة وأخبار سيئة. الموظفين: الجيدة! المدير: ما فيه تقديم. السيئة: الاجتماع طويل.", "rating": 4.2, "tags": ["اجتماع", "عمل"]},
    ],

    # ==================== HINDI ====================
    "hi_काम": [
        {"id": 37001, "text": "बॉस: 'तुम्हें ज्यादा पहल करनी चाहिए!' मैं घर चला गया।", "rating": 4.4, "tags": ["बॉस", "काम"]},
        {"id": 37002, "text": "डॉक्टर: 'रोज सुबह उठकर एक किलोमीटर दौड़ो।' मरीज: 'डॉक्टर साहब, मैं दौड़ नहीं सकता।' डॉक्टर: 'तो चलो।' मरीज: 'वो भी नहीं।' डॉक्टर: 'तो सो जाओ।'", "rating": 4.2, "tags": ["डॉक्टर", "आलस"]},
        {"id": 37003, "text": "पत्नी: 'तुम मुझसे प्यार करते हो?' पति: 'हाँ।' पत्नी: 'कितना?' पति: 'जितना तुम मेरी सैलरी से करती हो।'", "rating": 4.5, "tags": ["पत्नी", "पैसे"]},
        {"id": 37004, "text": "इंटरव्यू में: 'आपकी कमजोरी क्या है?' 'मैं बहुत ईमानदार हूँ।' 'मुझे ईमानदारी पसंद नहीं।' 'मुझे भी नहीं।'", "rating": 4.6, "tags": ["इंटरव्यू", "ईमानदारी"]},
        {"id": 37005, "text": "गुरुजी: 'बच्चो, क्या तुम परमेश्वर को देख सकते हो?' बच्चा: 'नहीं।' गुरुजी: 'तो यकीन करो कि वो है।' बच्चा: 'गुरुजी, क्या आप अपना दिमाग देख सकते हैं?' गुरुजी: 'नहीं।' बच्चा: 'बस।'", "rating": 4.3, "tags": ["स्कूल", "बच्चा"]},
        {"id": 37006, "text": "दोस्त: 'तेरी नौकरी कैसी चल रही है?' मैं: 'नौकरी नहीं चल रही, मैं चल रहा हूँ।'", "rating": 4.2, "tags": ["नौकरी", "थकान"]},
        {"id": 37007, "text": "अमीर बाप: 'बेटा, पैसे से खुशी नहीं मिलती।' बेटा: 'तो अपने पास रखो, मुझे दे दो, मैं ढूंढ लेता हूँ।'", "rating": 4.5, "tags": ["पैसे", "बाप"]},
        {"id": 37008, "text": "ससुर: 'बेटा, किस काम आए हो?' दामाद: 'सिर्फ आशीर्वाद लेने।' ससुर: 'अच्छा, ले लो और जल्दी चले जाओ।'", "rating": 4.3, "tags": ["ससुर", "दामाद"]},
        {"id": 37009, "text": "ट्रैफिक पुलिस: 'लाइसेंस दिखाओ।' ड्राइवर: 'साहब, आज ही सीख रहा हूँ, लाइसेंस कहाँ से आएगा?'", "rating": 4.1, "tags": ["ट्रैफिक", "ड्राइविंग"]},
        {"id": 37010, "text": "पड़ोसी: 'तुम्हारे कुत्ते ने मुझे काट लिया!' मैं: 'अच्छा, मैं उसे डांटता हूँ — ऐसा मत करना, पड़ोसी का खून है।'", "rating": 4.0, "tags": ["कुत्ता", "पड़ोसी"]},
        {"id": 37011, "text": "माँ: 'बेटा, शादी कब करेगा?' बेटा: 'जब कोई मिलेगी।' माँ: 'मैं ढूंढ रही हूँ।' बेटा: 'तब कभी नहीं।'", "rating": 4.4, "tags": ["शादी", "माँ"]},
        {"id": 37012, "text": "वेटर: 'सर, आपने बिल देखा?' ग्राहक: 'हाँ, इसीलिए रो रहा हूँ।'", "rating": 4.3, "tags": ["रेस्टोरेंट", "बिल"]},
        {"id": 37013, "text": "ऑफिस में: 'काम खत्म हो गया?' 'जो काम नहीं था, वो खत्म हो गया।'", "rating": 4.5, "tags": ["ऑफिस", "काम"]},
        {"id": 37014, "text": "दूल्हा: 'मैं तुम्हें चाँद तारे तोड़कर दूंगा।' दुल्हन: 'पहले EMI भर दो।'", "rating": 4.6, "tags": ["शादी", "EMI"]},
        {"id": 37015, "text": "एक आदमी ने सोचा: 'आज से मैं बदल जाऊंगा।' दूसरे दिन सोचा: 'कल से।'", "rating": 4.2, "tags": ["आलस", "प्रॉक्रास्टिनेशन"]},
        {"id": 37016, "text": "मेरा सपना है कि मेरा बॉस मेरे सपने में भी काम न दे।", "rating": 4.4, "tags": ["बॉस", "सपना"]},
        {"id": 37017, "text": "प्रधानमंत्री ने कहा: 'हर घर में रोजगार होगा।' मेरे घर में तो नौकरानी की जगह खाली है।", "rating": 4.3, "tags": ["राजनीति", "रोजगार"]},
        {"id": 37018, "text": "भारत में तीन चीज़ें कभी नहीं बदलतीं: ट्रैफिक, राजनीति और रिश्तेदारों के सवाल।", "rating": 4.5, "tags": ["भारत", "सच"]},
        {"id": 37019, "text": "सुबह उठना मुश्किल है। लेकिन जेब में पैसे न हों तो भागना पड़ता है।", "rating": 4.1, "tags": ["सुबह", "पैसे"]},
        {"id": 37020, "text": "जब मैंने HR से पूछा कि increment कब होगा, उसने कहा: 'आपकी increment मेरी increment पर निर्भर करती है।'", "rating": 4.4, "tags": ["HR", "increment"]},
    ],
}

# Clean up placeholder
if "de_sonstiges" in new_jokes and len(new_jokes["de_sonstiges"]) == 0:
    del new_jokes["de_sonstiges"]
if "es_trabajo" in new_jokes:
    pass  # keep it

# Add to db
for category, jokes in new_jokes.items():
    if category not in db:
        db[category] = jokes
        print(f"  + {category}: {len(jokes)} jokes")
    else:
        # Add only new IDs
        existing_ids = {j["id"] for j in db[category]}
        added = [j for j in jokes if j["id"] not in existing_ids]
        if added:
            db[category].extend(added)
            print(f"  + {category}: {len(added)} new jokes added")

with open(JOKES_DB, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

total = sum(len(v) for v in db.values())
cats = len(db)
print(f"\n✅ Total: {total} jokes in {cats} categories")
