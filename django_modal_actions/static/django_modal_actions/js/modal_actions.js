(function ($) {
  $(document).ready(function () {
    var $modal = $(
      '<div id="dma-modal-action" class="dma-modal" role="dialog" aria-modal="true"><div class="dma-modal-content"></div></div>',
    ).appendTo("body");
    var $modalContent = $modal.find(".dma-modal-content");
    var lastFocusedElement = null;

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
              _toggleFieldVisibility($fieldContainer, currentValue, config.show_on_values);
            }
            // For select elements
            else if ($dependentField.is('select')) {
              var currentValue = $dependentField.val();
              _toggleFieldVisibility($fieldContainer, currentValue, config.show_on_values);
            }
            // For other input types
            else {
              var currentValue = $dependentField.val();
              _toggleFieldVisibility($fieldContainer, currentValue, config.show_on_values);
            }

            // Add event listener to the dependent field
            $dependentField.on('change', function() {
              var newValue = null;

              if ($(this).is(':radio') || $(this).is(':checkbox')) {
                newValue = $form.find('[name="' + config.dependent_field + '"]:checked').val();
              } else {
                newValue = $(this).val();
              }

              _toggleFieldVisibility($fieldContainer, newValue, config.show_on_values);
            });
          }
        }
      });
    }

    function _toggleFieldVisibility($field, currentValue, showOnValues) {
      if (showOnValues.includes(currentValue)) {
        $field.show();
      } else {
        $field.hide();
      }
    }

    function _getFocusableElements($container) {
      return $container.find(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ).filter(':visible');
    }

    function _trapFocus() {
      var focusableElements = _getFocusableElements($modal);
      if (focusableElements.length === 0) {
        $modal.off('keydown.focustrap');
        return;
      }

      if (focusableElements.length === 1) {
        $modal.off('keydown.focustrap').on('keydown.focustrap', function(e) {
          if (e.key === 'Tab' || e.keyCode === 9) {
            e.preventDefault();
          }
        });
        return;
      }

      var firstFocusable = focusableElements.first();
      var lastFocusable = focusableElements.last();

      $modal.off('keydown.focustrap').on('keydown.focustrap', function(e) {
        if (e.key === 'Tab' || e.keyCode === 9) {
          if (e.shiftKey) {
            if (document.activeElement === firstFocusable[0]) {
              e.preventDefault();
              lastFocusable.focus();
            }
          } else {
            if (document.activeElement === lastFocusable[0]) {
              e.preventDefault();
              firstFocusable.focus();
            }
          }
        }
      });
    }

    function _closeModal() {
      $modal.hide();
      $modal.off('keydown.focustrap');
      $(document).off('keydown.dmaModal');
      if (lastFocusedElement) {
        lastFocusedElement.focus();
        lastFocusedElement = null;
      }
    }

    $(document).on("click", ".dma-modal-action-button", function (e) {
      e.preventDefault();
      lastFocusedElement = this;
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
        if (data.success !== undefined) {
          if (data.success) {
            location.reload();
          } else if (data.errors) {
            _displayErrors(data.errors);
          }
        } else if (data.content) {
          $modalContent.html(data.content);

          var $heading = $modalContent.find("h2");
          if ($heading.length) {
            var headingId = "dma-modal-heading-" + Date.now();
            $heading.attr("id", headingId);
            $modal.attr("aria-labelledby", headingId);
          } else {
            $modal.removeAttr("aria-labelledby");
            var modalTitle = $modalContent.find("h1, h2, h3").first().text() || "Dialog";
            $modal.attr("aria-label", modalTitle);
          }

          $modal.show();
          handleConditionalFields();

          var $firstFocusable = _getFocusableElements($modal).first();
          if ($firstFocusable.length) {
            $firstFocusable.focus();
          } else {
            $modal.find('h2').attr('tabindex', '-1').focus();
          }

          _trapFocus();

          $(document).off('keydown.dmaModal').on('keydown.dmaModal', function(e) {
            if (e.key === 'Escape' || e.keyCode === 27) {
              if ($modal.is(':visible')) {
                e.preventDefault();
                _closeModal();
              }
            }
          });
        }
      });
    });

    $(document).on(
      "click",
      "#dma-modal-action .cancel, #dma-modal-action .dma-modal-close",
      function (e) {
        e.preventDefault();
        _closeModal();
      },
    );

    function _displayErrors(errors) {
      $(".dma-errorlist, .dma-alert-danger").remove();

      var errorCount = Object.keys(errors).length;
      var $statusMessage = $(".dma-status-message");
      if ($statusMessage.length) {
        $statusMessage.text("");
        setTimeout(function() {
          $statusMessage.text("Form submission failed. " + errorCount + " error" + (errorCount > 1 ? "s" : "") + " found. Please review and correct.");
        }, 100);
      }

      $.each(errors, function (field, messages) {
        if (field === "__all__") {
          var $generalError = $(
            '<div class="dma-alert dma-alert-danger" role="alert"></div>',
          );
          $generalError.text(messages.join(" "));
          $("#dma-modal-action form").prepend($generalError);
        } else {
          var $field = $("#id_" + field);
          var $errorList = $('<ul class="dma-errorlist" role="alert"></ul>');
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

      if ($modal.is(':visible')) {
        _trapFocus();
      }
    }

    $(document).on("submit", "#dma-modal-action form", function (e) {
      e.preventDefault();
      var form = $(this);
      var url = form.attr("action");
      var formData = new FormData(form[0]);

      var $confirmBtn = form.closest("#dma-modal-action").find(".dma-confirm-btn");
      $confirmBtn.prop("disabled", true).addClass("dma-loading").attr("aria-busy", "true");
      $(".dma-status-message").text("Processing your request, please wait...");

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
        timeout: 30000,
        success: function (data) {
          if (data.success) {
            _closeModal();
            location.reload();
          } else if (data.errors) {
            $confirmBtn.prop("disabled", false).removeClass("dma-loading").attr("aria-busy", "false");
            _displayErrors(data.errors);
          }
        },
        error: function (jqXHR, textStatus, errorThrown) {
          $confirmBtn.prop("disabled", false).removeClass("dma-loading").attr("aria-busy", "false");
          if (textStatus === 'timeout') {
            _displayErrors({
              __all__: ["Request timed out. Please try again."],
            });
          } else {
            _displayErrors({
              __all__: ["An unexpected error occurred. Please try again."],
            });
          }
        },
      });
    });

    $(window).on("click", function (e) {
      if ($(e.target).is(".dma-modal")) {
        if (!$(".dma-confirm-btn").hasClass("dma-loading")) {
          _closeModal();
        }
      }
    });
  });
})(django.jQuery);
