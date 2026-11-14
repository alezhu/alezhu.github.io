---
title: "VirtualBox  и NEM на Windows 11 IoT Корпоративная  LTSC"
date: 2025-11-18 13:57:00
id: 181
original_url: https://alezhu.dreamwidth.org/181.html
security: public
tags:
  - virtualbox
  - soft
  - iопыт
  - windows11
  - windows
---

# VirtualBox  и NEM на Windows 11 IoT Корпоративная  LTSC

Купил китайский ноутбук Firebat U6B на AMD Ryzen 7 8745 дя работы. Поставил на него Windows 11 IoT Корпоративная  LTSC. Также поставил туда VirtualBox (на данный момент 7.2.<что-то там>). И VirtualBox запускает виртуалки в режиме софтовой эмуляции (NEM), хотя проц AMD-V поддерживает и в BIOS оно включено. То есть в статусбаре отображается черепашка, во всплывающей подсказке на черепашке есть строка «Execute Engine: native API», ну и в логах есть запись

> HM: HMR3Init: Attempting fall back to NEM: AMD-V is not available

Также проги systeminfo  и msinfo32 отображают у себя строку «Обнаружена низкоуровневая оболочка. Функции, необходимые для Hyper-V, отображены не будут.»

Ну, короче, все признаки того, что включен Hyper-V.

При этом я проделал почти все рекомендации чтобы его выключить, которые нашел, а именно:

1. Естественно всё, что касается Hyper-V, удалено из Windows Components
2. Выполнены команды **bcdedit /set hypervisorlaunchtype off**  и **bcdedit /set vsmlaunchtype Off**
3. Выполнена команда **DISM /Online /Disable-Feature:Microsoft-Hyper-V**
4. В настройках безопасности в Core Isolation выключено Memory Integrity
5. В реестре в разделе HKEY\_LOCAL\_MACHINE\System\CurrentControlSet\Control\DeviceGuard параметрам EnableVirtualizationBasedSecurity, HyperVVirtualizationBasedSecurityOptout присвоены нули
6. Там же в разделе Scenarios в подразделах HypervisorEnforcedCodeIntegrity, SystemGuard и WindowsHello (это кстати важно!) параметру Enabled тоже прописаны нули
7. В групповых настройках Virtualization Based Security также выключена

Ничего их этого не помогало. Ну или как минимум было недостаточно. И только случайный комментарий на reddit причем вообще [в теме](https://www.reddit.com/r/vmware/comments/1hr7vsm/vmware_detecting_hyperv_even_when_it_isnt_enabled/) про VMWare мне помог.

А именно:

1. Нужно скачать архив с «Device Guard and Credential Guard hardware readiness tool» [отсюда](https://www.microsoft.com/en-us/download/details.aspx?id=53337), распаковать его и запустить \*.ps1 скрипт из него (DG\_Readiness\*.ps1) с параметром -Disable.  По сути этот скрипт как раз делает почти все тоже, что было описано в пунктах выше, но ещё немного больше
2. Винда перезагрузится (или сделать это руками) и прямо во время загрузки (типа в консоли ) будет предложено выключить Credential Guard и потом Device Guard (или в обратном порядке) - надо там нажать F3 каждый раз. Я так понимаю это все отключается где-то на уровне UEFI
3. После этого винда загрузится с выключенным Hyper-V. Но если WindowsHello/Enable (см. выше) сделать 1, то VirtualBox опять будет использовать NEM. Не надо так.

ЗЫ. Отдельно хочется «плюнуть» в сторону Oracle. У них есть форум по VirtualBox и там есть [тема по отключению Hyper-V](https://forums.virtualbox.org/viewtopic.php?f=25&t=99390). Большинство рецептов взято оттуда. Но про скрипт от Microsoft там нет. Когда я нашел решение, я хотел им написать в эту тему про него. Для чего там надо зарегиться. Ок. Но зарегиться нельзя из-за санкций (помогает?). Ладно. У нас есть КВН. Зарегился, при попытке входа сайт стал выдавать BadRequest типа «браузер прислал запрос, который моя не понимать». Ладно. Зашел в Firefox. Когда зашел, кнопка отправки сообщения в теме пропала. Это, судя по всему, потому, что оно в разделе туториалов. Ладно. Хотел написать в директ топикстартеру про скрипт, чтобы он добавил инфу в тему, но похоже новорегам это сделать нельзя. Ладно.. Хотя какое «ладно». Идите вы нахер, короче, с вашими заморочками! Написал в жж-хе, поисковик проиндексирует, может кто-то найдет и ему поможет.
