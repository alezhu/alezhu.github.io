---
title: "Windows 7 Service Pack 1. Проблемы установки"
date: 2011-01-16 22:42:00
id: 143
original_url: https://alezhu.dreamwidth.org/143.html
security: public
---

# Windows 7 Service Pack 1. Проблемы установки

На днях Microsoft выпустила финальную версию первого сервис пака для Windows 7. Сервис пак доступен пока не всем, а только производителям железа и, я так понимаю, подписчикам MSDN. Для всех он выйдет где-то в начале февраля. Но на торрентах, естественно, уже все есть.
Так вот, попытка его поставить у меня неизменно приводила к ошибке "Не найдена сборка на которую имеется ссылка" (aka STATUS\_SXS\_ASSEMBLY\_MISSING aka 0x80073701). Ни какая сборка, ни чего делать - инфы не было. Поисковики ничего конкретного не говорили, а только намекали. Так что, если вы столкнулись с подобным - ниже план действий - глядишь да поможет.
Предполагаем, что винда стоит в папке c:\windows. Если не так - делайте поправку на свой путь.
Вначале идем и смотрим в файл лога установки c:\Windows\Logs\CBS\CBS.log. Смотрим в самый конец и ищем там первую строку, у которой тип сообщения не Info, а Error. У меня это выглядело примерно так

```
2011-01-15 20:15:00, Info                  CBS    Exec: Resolving Package: Microsoft-Windows-SampleContent-Music-Package~31bf3856ad364e35~x86~~6.1.7601.17514, Update: MusicSamples, PinDeployment: x86_microsoft-windows-s..nt-music-deployment_31bf3856ad364e35_6.1.7600.16385_none_21cd20ec32554018
2011-01-15 20:15:00, Error                 CSI    00000215@2011/1/15:17:15:00.782 (F) d:\w7rtm\base\wcp\componentstore\csd_locking.cpp(324): Error STATUS_SXS_ASSEMBLY_MISSING originated in function CCSDirectTransaction::LockComponent expression: (null)[gle=0x80004005]
2011-01-15 20:15:01, Error                 CSI    00000216 (F) STATUS_SXS_ASSEMBLY_MISSING #756421# from CCSDirectTransaction::OperateEnding at index 0 of 1 operations, disposition 2[gle=0xd015000c]
2011-01-15 20:15:01, Error                 CSI    00000217 (F) HRESULT_FROM_WIN32(ERROR_SXS_ASSEMBLY_MISSING) #756306# from Windows::ServicingAPI::CCSITransaction::ICSITransaction_PinDeployment(Flags = 0, a = Microsoft-Windows-SampleContent-Music-Deployment, Version = 6.1.7600.16385, pA = PROCESSOR_ARCHITECTURE_INTEL (0), Culture neutral, VersionScope = 1 nonSxS, PublicKeyToken = {l:8 b:31bf3856ad364e35}, Type neutral, TypeName neutral, PublicKey neutral, cb = (null), s = (null), rid = [95]"Microsoft-Windows-SampleContent-Music-Package~31bf3856ad364e35~x86~~6.1.7601.17514.MusicSamples", rah = (null), manpath = (null), catpath = (null), ed = 0, disp = 0)[gle=0x80073701]
```

Перед Error идет Info , в котором, в принципе, говорится о том, что пытались сделать. В моем случае это была попытка найти пакет Microsoft-Windows-SampleContent-Music-Package. Если у вас тоже ошибка при "Resolving Package" читайте дальше - иначе сорри.
Так вот, судя по всему, происходит попытка обновить этот пакет, а он не установлен. В моем случае это были примеры звуковых файлов, которые действительно из инсталятора были выкинуты ибо нафиг они нужны, только место занимать. Но SP1 их почему-то очень хочет.
Описания пакетов состоят из трех файлов - .cat, .mum и .manifest. Первые 2 лежат в c:\Windows\servicing\Packages\. Манифест - в c:\Windows\winsxs\Manifests\. Оба этих каталога имеют настройки безопасности, дающий полный доступ только сервису TrustedInstaller, а администраторам - только на чтение. Поэтому, если дальше по ходу пьесы, вам будет нужно что-то в них копировать - в настройках безопасности этих папок ставите Администратора владельцем и даете ему полный доступ (тут я подразумеваю, что все действия вы выполняете под Администратором).
Итак, в логе мы видим имя пакета Microsoft-Windows-SampleContent-Music-Package. Идем в c:\Windows\servicing\Packages\ и ищем там 2 файла .cut и .mum, начинающиеся на это имя и имеющие версию 6.1.7600.16385 (это тоже видно из лога, а версия 6.1.7601.17514 - это то, что входит в SP1). Если их там нет - нужно будет копировать из дистрибутива винды. Откуда и как - ниже, а пока запоминаем, что нам нужны эти файлы и идем в c:\Windows\winsxs\Manifests\, в котором ищем файл
"x86\_microsoft-windows-s..nt-music-deployment\_31bf3856ad364e35\_6.1.7600.16385\_none\_21cd20ec32554018.manifest" (именно так с точками в "s..nt") - имя тоже берется из лога. Если не находим, а скорее всего нет, значит надо его тоже выдирать из дистрибутива.
Допустим "дистриб" находится в папке d:\w7. Тогда открываем файл d:\w7\sources\install.wim в [7-zip](http://www.7-zip.org/) и видим там структуру каталогов, как она будет после установки. В частности, видим каталог Windows в нем есть servicing\Packages\ и winsxs\Manifests\. Соответственно, берем файлы .cut, .mum и .manifest, которых не хватало, из архива и переписываем их в нужные места установленный винды.
Вот такие нехитрые действия должны помочь избавиться от ошибки установки. Но возможно при этом будет другая ошибка, а именно в логе появится

```
SPI: (SPIRegQueryStringValue:700)Failed to query registry value: MiscString2 er=0x2
```

Лечится запуском

```
SFC /SCANNOW
```

Ну все. Happy Install =)
