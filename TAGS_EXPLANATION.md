## Explanation of Tags Used
<h3>1. Russian txt files:</h3>

| Tag          | Explanation               | Example
| -------------| --------------------------|-----------------------------------------------------  
| ```<end_verse_line>```   |The tag marks the end of a verse line. |Ты братецъ думаешь конечно справедливо.```<end_verse_line> ```                                                       
| ```<end_verse_line_interscene_rhyme>``` |The tag marks the end of the verse line when a verse line connects two scenes through rhyme|Ахъ! ваша мнѣ любовь — но           Свѣтознай идетъ.```<end_verse_line_interscene_rhyme>```<br>ЯВЛЕНІЕ 8.<br> И онъ во мнѣ любовь такую же найдетъ.```<end_verse_line_interscene_rhyme>```
|```<cast [character_names]>```|The tag specifies the dramatic characters present in the scene.|```<cast ОЛЬГА, СВѢТОЗНАЙ>```                                    
|```<extra_SCENE>```|The tag marks a new scene that corresponds<br>to an entrance or an exit of a dramatic character<br>and does not correspond to the division into scnenes in the publication.|Что вижу, Свѣтознай? нечаянно явленье.<br>```<extra_SCENE>``` ```<cast ЭРАСТЪ, СВѢТОЗНАЙ>```<br>СВѢТОЗНАЙ.<br>Любезнѣйшій Эрастъ! въ какомъ я восхищеньи,```<end_verse_line>```<br>
|```<no_change_SCENE>```|The tag marks such a scene where all dramatic characters are the same as in the preceding scene|ЯВЛЕНІЕ ТРЕТІЕ. ```<no_change_SCENE>``` 
|```<collective_number [number]>```|This tag specifies the collective number of a character, if applicable.For example, two guards are counted as 1 if they appear and speak only together and as 2 if they speak or appear separately.|СЛУГИ Доброна ```<collective_number 1>```
|```<alternative_name [name]>```|The tag specifies an alternative name under<br>which a dramatic character appears in the play.|АНИСЬЯ ДМИТРІЕВНА КАМСКАЯ, ```<alternative_name АНИСЬЯ ДМИТРІЕВНА>```
| ```<stage></stage>```|These two tags mark the beginning and end of a stage direction following Sperantov's markup.|```<stage>```(въ сторону.)```</stage> ```
|```<not_listed_character [name]>```|The tag is used to indicate dramatic characters who appear in the play but are not listed in the list <br> of dramatic characters.|```<not_listed_character КАТЯ>```
|```<intermedia> </intermedia>```|The tag marks the beginning and end of the intermedia text.|```<intermedia>```ИНТЕРМЕДИЯ ПЕРВАЯ. ДВѢ ДѢВУШКИ ТАНЦУЮТЪ СЪ ТАМБУРИНОМЪ.```</intermedia>```
|```<prose></prose>```|The tags marks the beginning and end of the fragment in prose.|```<prose>```„Государь мой!Боюсь, естьли вы вскоре не пріѣдете за ЧестнодумомЪ```</prose>```
|```<stage_seprator>```|The tag denotes that the action continues on a different stage.|Увидишь ты, что я отнюдь не измѣню...```<end_verse_line>``` ```<stage>```Продолжаютъ разговоръ тихо</stage>.<br>```<stage_seprator> ```ГАРПЕНКО,```<stage>```будто споря съ кѣмъ.</stage> 
|```<speaker_clarification [character]>```|The tag clarifies which characters are speaking.| ВСѢ.```<speaker_clarification character СЕРГѢЕВЪ, ФИГУРИНЪ, ГАРПЕНКО, ПАЩЕНКО>``` 
|```<speaking_character_no_utterance [character]>```|The tag marks a character who is speaking in a particular scene, which could be specified in the stage direction, but does not make an utterance.|```<speaking_character_no_utterance ТУРУХТАНОВА>```


<h3>2. Russian TEI files:</h3>
The TEI files were obtained from https://dracor.org/rus. However, to meet our research goals, the following markup tags have been added or modified:

| Tag          | Explanation               | Example
| -------------| --------------------------|----------------------------------------------------- 
|```<collective_number></collective_number>```|This tag specifies the collective number of a character, if applicable. For example, two guards are counted as 1 if they appear and speak only together and as 2 if they speak or appear separately.|```<persName>```Гости```</persName>``` ```<collective_number>```1```</collective_number>```
|```<div type="extra_scene" cast=[characters]>```|These tags mark a new scene that corresponds<br>to an entrance or an exit of a dramatic character<br>and does not correspond to the division into scnenes in the publication. Additionally, they specify the dramatic characters who are on stage.|```<div type="extra_scene" cast="Лиза, София, Фамусов">```
|```<div type="complex_scene" cast="Лиза, София">```|This combination of tags marks such instances when the names of the dramatic characters listed in the first stage direction of the scene do not match the dramatic characters who actually appear on stage, so it becomes necessary to list them excplicitly.|``` <div type="complex_scene" cast="Лиза, София">```

<h3>3. French TEI files:</h3>
The TEI files were obtained from http://www.theatre-classique.fr/. The following modifications were made:

| Tag          | Explanation               | Example
| -------------| --------------------------|-----------------------------------------------------
|```<div2 type="extra_scene" cast=[names]>```|These tags mark a new scene that corresponds to an entrance or an exit of a dramatic character and does not correspond to the division into scnenes in the publication. Additionally, they specify the dramatic characters who are on stage.|```<div2 type="extra_scene" cast="ALIDOR, CLÉANDRE">```
|```<div2 type="complex_scene" cast=[names]>```|This combination of tags marks such instances when the names of the dramatic characters listed in the first stage direction of the scene do not match the dramatic characters who actually appear on stage, so it becomes necessary to list them excplicitly, or the dramatic characters are not listed for a particular scene.|```<div2 type="complex_scene" n="7" cast="ALIDOR, ANGÉLIQUE, DORASTE, PHILIS, CLÉANDRE">```
|```<div1 type='inner_comedy'>```|This tag is reserved for comedies within comedies.|```<div1 type='inner_comedy'>```<head>DIVORCE COMIQUE</head>
|```<castItem_extra>```|The tag is used for the dramatic characters who appear in the inner comedy and do not appear in the main comedy.|```<castItem_extra>```<role_extra id='FLORIMONT' sex='1' type='H' statut='comédien' age='A' stat_amour='néant'>FLORIMONT</role_extra>,comédien.```</castItem>```

<h3>2. French Word Documents:</h3>

| Tag          | Explanation               | Example
| -------------| --------------------------|-----------------------------------------------------
|LES ACTEURS | This tag marks the beginning of the list of all dramatic characters who are present in the play|**LES ACTEURS** <br> LÉLIE <br>ÉRASTE
|[dramatic character name] integer | This pattern is used for collective dramatic characters to indicate if they should be counted as one dramatic character or as many|DEUX LAQUAIS 1|
|```/SCENE/ ```|This tag marks a new scene that corresponds to an entrance or an exit of a dramatic character and does match the division into scnenes in the publication.|```/SCENE/``` TAMPONET
|```*SCENE 7*```|The tag marks such a scene where all dramatic characters are the same as in the preceding scene.|```*SCENE 7*```<br>JULIEN<br>STÉPHANE
|МОЛЧИТ | The tag indicates a non-speaking dramatic character in a scene |JULIEN - МОЛЧИТ

<h3>3. Generic Word Documents:</h3>

| Tag          | Explanation               | Example
| -------------| --------------------------|-----------------------------------------------------
|DRAMATIC CHARACTERS | This tag marks the beginning of the list of all dramatic characters who are present in the play|**DRAMATIC CHARACTERS** <br> DONNA FLORIDA  <br>IL CONTE ROBERTO 
|[dramatic character name] integer | This pattern is used for collective dramatic characters to indicate if they should be counted as one dramatic character or as many|QUATTRO SERVI DI MACHMUT 1
|```/SCENE/ ```|This tag marks a new scene that corresponds to an entrance or an exit of a dramatic character and does match the division into scnenes in the publication.|```/SCENE/``` DONNA FLORIDA 
|```*SCENE 7*```|The tag marks such a scene where all dramatic characters are the same as in the preceding scene.|```*SCENE 7*```*SCENE 4* <br>GRAF VON SCHLAMM<br>BARON WURM
|NON_SPEAKING| The tag indicates a non-speaking dramatic character in a scene |GANDOLFO - NON_SPEAKING

<h3>4. Shakespeare TEI files:
The TEI files were obtained from https://dracor.org/shake. The following modifications were made:
| Tag          | Explanation               | Example
| -------------| --------------------------|-----------------------------------------------------
|```<div type="extra_scene" cast=[names]>```|These tags mark a new scene that corresponds to an entrance or an exit of a dramatic character and does not correspond to the division into scnenes in the publication. Additionally, they specify the dramatic characters who are on stage.|```<div type="extra_scene", cast="#Proteus_TGV #Speed_TGV">```
