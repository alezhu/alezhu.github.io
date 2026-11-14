---
title: "jQuery Dialog + Upload file"
date: 2009-11-15 13:53:00
id: 106
original_url: https://alezhu.dreamwidth.org/106.html
security: public
tags:
  - программист
  - jquery
  - .net
  - asp.net
mood: "ворочу горы"
---

# jQuery Dialog + Upload file

Столкнулся с занятным глюком. Мне нужно было при клике на ссылку показать модальный диалог с полем для загрузки файла и после нажатия OK отправить это файл на сервер. Дабы не изобретать велосипед, для показа диалога решил воспользоваться [jQuery](http://jquery.com/) и соотвественно [jQuery UI Dialog](http://jqueryui.com/demos/dialog/). Но все оказалось немного сложнее.

Но давайте поподробнее с самого начала и с примерами чтобы прочувствовать все самим =). Для серверной части я использую обычный ASP.NET и файл буду грузить обычной синхронной отправкой без всяких там AJAX.

Итак, создадим в Visual Studio обычный WebSite. На Default.aspx поместим ссылку, Label, FileUpload, кнопку отправки формы и еще одну ссылку. Label нам нужен для вывода имени загруженного файла, первая ссылка - для показа диалога, вторая - для отправки формы через JavaScript (только в качестве примера) и кнопка отправки формы для проверки того, что отправка работает. Причем FileUpload обернем в div с id="dialog" - это и будет в дальнейшем содержимое нашего диалога.
Код страницы будет примерно таким:
> `1. <form id="form1" runat="server">
> 2. <div>
> 3. <asp:Label ID="Label1" runat="server" Text="Select file"></asp:Label><br />
> 4. For show dialog click <a id="showLink" href="http://www.asp.net/">this link.</a>
> 5. <div id="dialog">
> 6. <asp:FileUpload ID="FileUpload1" runat="server" />
> 7. </div>
> 8. <input type="submit" value="Отправить" />
> 9. For upload file click <a id="sendLink" href="http://www.asp.net/">this link.</a>
> 10. </div>
> 11. </form>
> * This source code was highlighted with Source Code Highlighter.`

Далее в методе Page\_Load пишем такой код:

> `1. protected void Page_Load(object sender, EventArgs e)
> 2. {
> 3. if (IsPostBack)
> 4. {
> 5. if (this.FileUpload1.HasFile)
> 6. {
> 7. Label1.Text = string.Format("You files name is {0}.", FileUpload1.FileName);
> 8. }
> 9. else
> 10. {
> 11. Label1.Text = "No file has been uploaded";
> 12. }
> 13. }
> 14. }
> * This source code was highlighted with Source Code Highlighter.`

Теперь можно запустить сайт, выбрать файл, нажать кнопку отправки и убедиться, что в Label появляется имя загружаемого файла, из чего можно сделать вывод, что файл отправляется на сервер.

Теперь добавим библиотеки JQuery и JQuery UI, для чего скачаем их с соответствующих сайтов, поместим в каталог проекта и пропишем ссылки на них в секции HEAD нашей страницы. Можно также их не качать, а прописать ссылки на Google вот так:

```html
<link href="~/css/base/jquery-ui.css" rel="stylesheet" type="text/css" />
<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js" type="text/javascript"></script>
<script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>
```

Хотя JQueryUI вам все равно лучше скачать, причем версию для разработчиков, так как там идет базовый набор css. Или можно там же на сайте скачать другую тему или создать свою. Но нам для теста хватит базовой - она, как вы видите, и указана в аттрибуте link в коде выше.

Так jQuery мы подключили, давайте теперь задействуем его для наших ссылок. Пишем на нашей странице в секции head следующий код:

```javascript
$(document).ready(
  function() {
    $("#showLink").click(
      ShowDialog
    );
    $("#sendLink").click(
      submitForm
    );
  }
);

var submitForm = function() {
  var form = window.theForm;
  if (!form) form = document.forms[0];
  if (form) form.submit();
  return false;
}

var ShowDialog = function() {
  var dlg = $("#dialog");
  dlg.dialog(
    {
      position: 'center',
      buttons: {
        'Отмена': function() {
          $(this).dialog('close');
        },
        'OK': function() {
          submitForm();
        }
      },
      modal: true,
      width: 400
    }
  );
  dlg.dialog('open');
  return false;
}
```

Здесь мы вешаем на клик ссылок вызовы функций показа диалога и отправки формы, а также определяем сами функции. Имхо все довольно прозрачно. Теперь попробуйте запустить сайт и отправить файл кнопкой Отправить и ссылкой. Все должно работать как и раньше.

А теперь попробуйте ткнуть ссылку показа диалога - появится модальный диалог с нашим полем для ввода файла. Выберите файл и нажмите OK. Вот тут и появляется сюрприз - файл не отправляется на сервер!

Причину я нашел не сразу, хотя оказалась она довольно банальна - оказалось что при создании диалога jQuery выносит div с id="dialog" и все его содержимое из того места, где div был описан, в конец страницы. Таким образом, получается, что input для загрузки файла находится вне тэга form, и когда мы делаем форме submit, то естественно этот input не участвует в формировании тех параметров, что передаются серверу.

Для борьбы с этой напастью я первоначально решил внутри div'а для диалога сунуть еще один form, а внутри него уже FileUpload, наивно полагая, что jQuery вынесет и эту форму за пределы первоначальной , а "сабмитить" я уже буду вторую форму. Нет jQuery конечно форму вынес (причемкак-то странно, потому что при этом образовалась копия первой формы), но input при этом оказался не внутри этой формы, а после нее. То есть отправка второй формы тоже ничего не давала.

В итоге я решил от второй формы отказаться, а просто перед отправкой возвращать input с файлом обратно внутрь первоначальной формы. Для этого код обработки нажатия кнопки OK меняется на такой:
> `1. 'OK': function() {
> 2. var files = $("#<%= FileUpload1.ClientID %>");
> 3. if (files && files.length > 0) {
> 4. var form = window.theForm;
> 5. if (!form) form = document.forms[0];
> 6. if (form) {
> 7. form.appendChild(files[0]);
> 8. submitForm();
> 9. }
> 10. }
> 11. dlg.dialog('close');
> 12. }
> * This source code was highlighted with Source Code Highlighter.`

Как можно убедиться, теперь файл на сервер отсылается.


*Настроение:* ворочу горы
