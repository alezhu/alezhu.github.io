---
title: "Enterprise Library Custom Logger"
date: 2011-01-10 00:08:00
id: 142
original_url: https://alezhu.dreamwidth.org/142.html
security: public
tags:
  - программист
  - iопыт
  - .net
---

# Enterprise Library Custom Logger

Изучаю тут помаленьку [Enterprise Library](http://entlib.codeplex.com). Книжку читаю по нему и экспериментирую. [Книжка](http://www.bgshop.ru/Details.aspx?id=9579325), кстати, так себе - могла бы быть и поглубже. Но речь не о ней.
Итак, в Enterprise Library есть модуль логирования. Работает примерно так. В своем приложении вы получаете экземпляр "Писателя в лог" (LogWriter) и вызываете у него одну из перегрузок из метода Write:
> `1. LogWriter writer = EnterpriseLibraryContainer.Current.GetInstance<LogWriter>();
> 2. writer.Write(...);
> * This source code was highlighted with Source Code Highlighter.`

"Писатель" берет из настроек приложения указанного "читателя" (или "слушателя" - потому, что классы имею в названии Listener) и передает ему запись типа LogEntry. "Слушатель" преобразует запись LogEntry с использованием заданного в настройках приложения.. "форматировщика" (класс, который реализует интерфейс ILogFormatter) и выводит полученное куда-нибудь (это зависит от типа "слушателя" - в файл, в базу данных, в журнал событий Windows и т.д.).
Так вот, решил я воспользоваться этой функциональностью, чтобы просто выводить сообщения в консоль. Причем выводить только само сообщение. Как такое можно сделать?
1й вариант в качестве слушателя назначить System Diagnostics Trace Listener (класс SystemDiagnosticsTraceListenerData). При этом в качестве TraceListener ему назначить класс System.Diagnostics.ConsoleTraceListener. Все работает, но вместо простого сообщения выводится полная информация по сообщению - время создания, категория, имя машины и пользователя и так далее - короче все поля класса LogEntry. И при этом гадость в том, что для System Diagnostics Trace Listener нельзя назначить "форматировщика".
Тогда 2ой вариант - пишем собственного слушателя. Наследуем его от CustomTraceListener. А поскольку родитель наш - абстрактный класс, то "студия" предлагает сразу реализовать 2 его метода Write и WriteLine. Получается как то так:
> `1. using System;
> 2. using System.Diagnostics;
> 3. using Microsoft.Practices.EnterpriseLibrary.Common.Configuration;
> 4. using Microsoft.Practices.EnterpriseLibrary.Logging;
> 5. using Microsoft.Practices.EnterpriseLibrary.Logging.Configuration;
> 6. using Microsoft.Practices.EnterpriseLibrary.Logging.TraceListeners;
> 8. namespace EntLibExt.Logging
> 9. {
> 10. [ConfigurationElementType(typeof(CustomTraceListenerData))]
> 11. public class ConsoleTraceListener : CustomTraceListener
> 12. {
> 13. public override void Write(string message)
> 14. {
> 15. Console.Write(message);
> 16. }
> 18. public override void WriteLine(string message)
> 19. {
> 20. Console.WriteLine(message);
> 21. }
> 22. }
> 23. }
> * This source code was highlighted with Source Code Highlighter.`

C виду казалось, что все просто. У CustomTraceListener есть свойство типа Formatter, ему мы назначаем класс TextFormatter, а в шаблоне для последнего прописываем просто {message}.
Компилим, все работает, за исключением того, что шаблон игнорируется и все равно выводятся все поля класса LogEntry.
Ладно, хотя это оказалось и неправильно, я сделал еще 3й вариант и создал свой собственный "форматировщик", который из всей LogEntry выводил только Message. Но прикол был в том, что метод моего "форматировщика" просто не вызывался.
Гугл мне не помог ничем, поэтому я пошел просить помощи у отладчика.
В отладчике нарисовалась интересная картина: CustomTraceListener вызывает для переданной ему LogEntry метод ToString(), а тот в свою очередь просто берет создает TextFormatter с шаблоном по умолчанию (там где все поля) и вызывает его метод форматирования - результат выводит через методы Write и WriteLine (в которых я это дело пишу в консоль). Иными словами, заданный в настройках приложения "форматировщик" просто игнорируется.
Я уж было продумал, что у меня какая-то не такая Enterprise Library, и вместо своего ConsoleTraceListener поставил стандартный FlatFileTraceListener. И о чудо! - в файл записалось только само сообщение. Дальнейший анализ показал, что во FlatFileTraceListener переопределен метод TraceData, в котором и вызывается "форматировщик". Таким образом, я вернулся к варианту 2, слегка его доработав, и все заработало как надо. Рабочий вариант класса "слушателя" для вывода в консоль с поддержкой форматирования выглядит так:
> `1. using System;
> 2. using System.Diagnostics;
> 3. using Microsoft.Practices.EnterpriseLibrary.Common.Configuration;
> 4. using Microsoft.Practices.EnterpriseLibrary.Logging;
> 5. using Microsoft.Practices.EnterpriseLibrary.Logging.Configuration;
> 6. using Microsoft.Practices.EnterpriseLibrary.Logging.TraceListeners;
> 8. namespace EntLibExt.Logging
> 9. {
> 10. [ConfigurationElementType(typeof(CustomTraceListenerData))]
> 11. public class ConsoleTraceListener : CustomTraceListener
> 12. {
> 13. public override void Write(string message)
> 14. {
> 15. Console.Write(message);
> 16. }
> 18. public override void WriteLine(string message)
> 19. {
> 20. Console.WriteLine(message);
> 21. }
>
> 24. public override void TraceData(TraceEventCache eventCache, string source, TraceEventType eventType, int id, object data)
> 25. {
> 26. if (this.Filter == null || this.Filter.ShouldTrace(eventCache, source, eventType, id, null, null, data, null))
> 27. {
> 29. if (data is LogEntry)
> 30. {
> 31. if (this.Formatter != null)
> 32. {
> 33. this.WriteLine(this.Formatter.Format(data as LogEntry));
> 34. }
> 35. else
> 36. {
> 37. base.TraceData(eventCache, source, eventType, id, data);
> 38. }
> 39. }
> 40. else
> 41. {
> 42. base.TraceData(eventCache, source, eventType, id, data);
> 43. }
> 45. }
> 46. }
> 48. }
> 49. }
> * This source code was highlighted with Source Code Highlighter.`

Как мне кажется, налицо недоработка разработчиков Enterprise Library. Хотя метод решения прост и в принципе естественен, но все-таки, раз есть поле для "форматировщика" грамотнее было бы его использовать по умолчанию.
