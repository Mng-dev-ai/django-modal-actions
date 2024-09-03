(function ($) {
  $(document).ready(function () {
    var $modal = $(
      '<div id="dma-modal-action" class="dma-modal"><div class="dma-modal-content"></div></div>',
    ).appendTo("body");
    var $modalContent = $modal.find(".dma-modal-content");

    $(document).on("click", ".dma-modal-action-button", function (e) {
      e.preventDefault();
      var url = $(this).attr("href");
      var isListAction = url.includes("list-modal-action");

      if (isListAction) {
        var selectedIds = [];
        $('input[name="_selected_action"]:checked').each(function () {
          selectedIds.push($(this).val());
        });
        url += "?selected_ids=" + JSON.stringify(selectedIds);
      }
      $.get(url, function (data) {
        $modalContent.html(data.content);
        $modal.show();
      });
    });

    $(document).on(
      "click",
      "#dma-modal-action .cancel, #dma-modal-action .dma-modal-close",
      function (e) {
        e.preventDefault();
        $modal.hide();
      },
    );

    function displayErrors(errors) {
      $(".dma-errorlist, .dma-alert-danger").remove();

      $.each(errors, function (field, messages) {
        if (field === "__all__") {
          var $generalError = $(
            '<div class="dma-alert dma-alert-danger" role="alert"></div>',
          );
          $generalError.text(messages.join(" "));
          $("#dma-modal-action form").prepend($generalError);
        } else {
          var $field = $("#id_" + field);
          var $errorList = $('<ul class="dma-errorlist"></ul>');
          $.each(messages, function (index, message) {
            $errorList.append($("<li></li>").text(message));
          });
          $field.before($errorList);
        }
      });

      if (Object.keys(errors).length > 0 && !errors.hasOwnProperty("__all__")) {
        var $generalError = $(
          '<div class="dma-alert dma-alert-danger" role="alert">Please correct the errors below.</div>',
        );
        $("#dma-modal-action form").prepend($generalError);
      }
    }

    $(document).on("submit", "#dma-modal-action form", function (e) {
      e.preventDefault();
      var form = $(this);
      var url = form.attr("action");
      var formData = new FormData(form[0]);

      var selectedIds = form.find('input[name="selected_ids"]').val();
      if (selectedIds) {
        formData.append("selected_ids", selectedIds);
      }
      $.ajax({
        url: url,
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        dataType: "json",
        success: function (data) {
          if (data.success) {
            $modal.hide();
            location.reload();
          } else if (data.errors) {
            displayErrors(data.errors);
          }
        },
        error: function (jqXHR, textStatus, errorThrown) {
          displayErrors({
            __all__: ["An unexpected error occurred. Please try again."],
          });
        },
      });
    });

    $(window).on("click", function (e) {
      if ($(e.target).is(".dma-modal")) {
        $modal.hide();
      }
    });
  });
})(django.jQuery);
