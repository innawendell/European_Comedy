## Explanation of Tags Used
1. Russian txt files:

| Tag                | Explanation                           | Example
| ------------------ | ------------------------------------- |------------- 
| <end_verse_line>   | The tag marks the end of a verse line. |Ты братецъ думаешь конечно справедливо. <end_verse_line>                                                        
| <end_verse_line_interscene_rhyme> |The tag marks the end of the verse <br>line when a verse line connects two scenes through rhyme|Ахъ! ваша мнѣ любовь — но           Свѣтознай идетъ.<br>ЯВЛЕНІЕ 8.<br> И онъ во мнѣ любовь такую же найдетъ.<end_verse_line_interscene_rhyme>
|<cast [character_names]>| The tag specifies the dramatic characters present<br> in the scene.|<cast ОЛЬГА, СВѢТОЗНАЙ>                                    
|<extra_SCENE>|The tag marks a new scene that corresponds<br>to an entrance or an exit of a dramatic character<br>and does not correspond to the division into scnenes in the publication.|Что вижу, Свѣтознай? нечаянно явленье.<br><extra_SCENE> <cast ЭРАСТЪ, СВѢТОЗНАЙ><br>СВѢТОЗНАЙ.<br>Любезнѣйшій Эрастъ! въ какомъ я восхищеньи,<end_verse_line><br>
|<no_change_SCENE>|The tag marks such a scene where all dramatic characters <br>are the same as in the preceding scene|ЯВЛЕНІЕ ТРЕТІЕ. <no_change_SCENE> 
|<collective_number [number]>|This tag specifies the collective number of a character, if applicable.<br>For example, two guards are counted as 1 if they appear and speak only together and as 2 if they speak or appear separately.|СЛУГИ Доброна <collective_number 1>
|<alternative_name [name]>|The tag specifies an alternative name under<br>which a dramatic character appears in the play.|АНИСЬЯ ДМИТРІЕВНА КАМСКАЯ, <alternative_name АНИСЬЯ ДМИТРІЕВНА>
|"<stage>"…"</stage>"|These two tags mark the beginning and end of a stage direction <br>following Sperantov's markup.|<stage>(въ сторону.)</stage> 
