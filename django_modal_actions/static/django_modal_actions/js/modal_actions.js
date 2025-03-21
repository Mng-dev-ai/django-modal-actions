(function ($) {
  $(document).ready(function () {
    var $modal = $(
      '<div id="dma-modal-action" class="dma-modal"><div class="dma-modal-content"></div></div>',
    ).appendTo("body");
    var $modalContent = $modal.find(".dma-modal-content");

    // Function to handle conditional fields visibility
    function handleConditionalFields() {
      var $form = $("#dma-modal-form");
      if (!$form.length) return;
      
      var conditionalFieldsData = {};
      try {
        conditionalFieldsData = JSON.parse($form.attr("data-conditional-fields") || "{}");
      } catch (e) {
        console.error("Error parsing conditional fields data:", e);
        return;
      }
      
      // Process each conditional field
      $.each(conditionalFieldsData, function(fieldName, config) {
        var $field = $form.find('[name="' + fieldName + '"]');
        var $fieldContainer = $field.closest('p');
        
        if ($field.length && $fieldContainer.length) {
          // Get the current value of the dependent field
          var $dependentField = $form.find('[name="' + config.dependent_field + '"]');
          
          if ($dependentField.length) {
            // For radio buttons and checkboxes
            if ($dependentField.is(':radio') || $dependentField.is(':checkbox')) {
              var currentValue = $form.find('[name="' + config.dependent_field + '"]:checked').val();
              toggleFieldVisibility($fieldContainer, currentValue, config.show_on_values);
            } 
            // For select elements
            else if ($dependentField.is('select')) {
              var currentValue = $dependentField.val();
              toggleFieldVisibility($fieldContainer, currentValue, config.show_on_values);
            }
            // For other input types
            else {
              var currentValue = $dependentField.val();
              toggleFieldVisibility($fieldContainer, currentValue, config.show_on_values);
            }
            
            // Add event listener to the dependent field
            $dependentField.on('change', function() {
              var newValue = null;
              
              if ($(this).is(':radio') || $(this).is(':checkbox')) {
                newValue = $form.find('[name="' + config.dependent_field + '"]:checked').val();
              } else {
                newValue = $(this).val();
              }
              
              toggleFieldVisibility($fieldContainer, newValue, config.show_on_values);
            });
          }
        }
      });
      
      // Helper function to toggle field visibility
      function toggleFieldVisibility($field, currentValue, showOnValues) {
        if (showOnValues.includes(currentValue)) {
          $field.show();
        } else {
          $field.hide();
        }
      }
    }

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
        // Initialize conditional fields after modal content is loaded
        handleConditionalFields();
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
