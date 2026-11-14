---
title: "Установка SAP Business One Studio Addon для Microsoft Visual Studio 2017 (Community Edition)"
date: 2017-07-26 20:22:00
id: 171
original_url: https://alezhu.dreamwidth.org/171.html
security: public
tags:
  - #ятестируюновыйредактор
---

# Установка SAP Business One Studio Addon для Microsoft Visual Studio 2017 (Community Edition)

При установке SAP Business One Studio есть возможность поставить Addon  под MS Visual Studio. Для этого MS Visual Studio должна уже быть установлена. Причем на июль 2017 года SAP B1 позволяет внедряться только в версии 10,11 и 12 (это, соответственно, VS2010,VS2012 и VS2013). При том что Microsoft уже выпустила VS2015 (14) и VS2017(15). Но если у вас последние, установщик SAP B1 Studio addon не поставит (или не даст выбрать если Custom-установка)

При этом  такая же ерунда была и на предыдущих версиях B1, когда SAP поддерживал только VS2010. Люди обходили это [путем временной смены версии  VS в реестре Windows на 10](https://archive.sap.com/discussions/thread/3805240).

Но с VS2017 это не прокатывает. Причина, скорее всего в том,что Microsoft не пишет при установке VS2017 путь до исполняемого файла. Во всяком случае не пишет его туда, куда раньше писала, а именно в HKEY\_CURRENT\_USER\Software\Microsoft\VisualStudio\<версия>\_Config\InstallDir

Установщик же SAP B1 Studio завязан на этот ключ реестра. В нем он берет каталог и ищет в этом каталоге файл devenv.exe (это как раз файл студии). И если не находит, то addon свой не ставит.

Таким образом, первый шаг состоит в том чтобы создать нужный ключ в реестре и прописать в него правильный путь до каталога. Поскольку установщик SAP B1 ищет только версии 10,11 и 12, то и брать нужно одну из них для пути к ключу. Например, в HKEY\_CURRENT\_USER\Software\Microsoft\VisualStudio создаем раздел 10.0\_Config, а в нем строковый параметр InstallDir . В сам параметр прописываем путь до каталога с devenv.exe (для VS2017 Community Editon это c:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\IDE)

После этого установщик поставит свой Addon, но Visual Studio все равно при создании нового проекта не будет проектов SAP Business One. Здесь причина в том, что Microsoft поменяла логику поиска сторонних шаблонов для проектов и их частей (items) .

Установщик SAP B1 Studio положит шаблоны своих проектов в c:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\IDE\ProjectTemplates\ в подпапки Csharp и  VisualBasic в папки SAP Business One. Аналогично для частей проектов будет использован каталог c:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\IDE\ItemTemplates. Согласно новой политики Microsoft необходимо перенести эти шаблоны в соответствующие папки в Visual Studio 2017\Templates в папке МоиДокументы.

Например, пользователя зовут Vova. Его папка с документами лежит в c:\Users\Vova\Documents\. В ней есть папка Visual Studio 2017, в ней папка Templates. Таким образом, мы берем папку c:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\IDE\ProjectTemplates\CSharp\SAP Business One и переносим ее в c:\Users\Vova\Documents\Visual Studio 2017\Templates\ProjectTemplates\Visual C#\ (для переноса, возможно, понадобятся права администратора).

Аналогично, c:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\IDE\ProjectTemplates\VisualBasic\SAP Business One переносим в c:\Users\Vova\Documents\Visual Studio 2017\Templates\ProjectTemplates\Visual Basic\.

Далее c:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\IDE\ItemTemplates\CSharp\SAP Business One переносим в c:\Users\Vova\Documents\Visual Studio 2017\Templates\ItemTemplates\Visual C#\, а c:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\IDE\ItemTemplates\VisualBasic\SAP Business One — в c:\Users\Vova\Documents\Visual Studio 2017\Templates\ItemTemplates\Visual Basic\

Естественно, если Visual Basic вы трогать не собираетесь, можно его папки не переносить. И также для C#.

В заключение нужно пойти в c:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\IDE\ и запустить там devenv.exe с ключом /installvstemplates
