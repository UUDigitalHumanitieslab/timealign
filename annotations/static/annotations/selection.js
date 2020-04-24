$(function() {
    function selectWord() {
        var selected = $("select[name=words]").val() || [];
        if ($(this).hasClass("selected")) {
            var index = selected.indexOf($(this).attr("data-pk"));
            selected.splice(index, 1);
            $(this).removeClass("selected");
        }
        else {
            selected.push($(this).attr("data-pk"));
            $(this).addClass("selected");
        }

        $("select[name=words]").val(selected);
    }

    function selectSegment() {
        $(this).toggleClass("endpoint");

        // select segment after two points were chosen (start and end)
        if ($(".endpoint").length > 1) {
            // mark all the words between the endpoints
            var segment = $(".endpoint").first().nextUntil(".endpoint").addBack(); // add start word
            segment = segment.add(segment.last().next());  // add final word
            segment.toggleClass("selected");

            $(".endpoint").removeClass("endpoint"); // remove highlight
        }

        var selected = $('.selected').map(function (_, el) { return $(el).data('pk') }).get();
        $("select[name=words]").val(selected);
    }

    var clickHandler = selectWord;
    $("#select-word").click(function() {
        clickHandler = selectWord;
        $("#select-word").addClass("active");
        $("#select-segment").removeClass("active");
        $("input[name=select_segment]").val(false);
    });
    $("#select-segment").click(function() {
        clickHandler = selectSegment;
        $("#select-word").removeClass("active");
        $("#select-segment").addClass("active");
        $("input[name=select_segment]").val(true);
    });
    $(".selectable .word").click(function() {
        clickHandler.call(this);
    });

    if ($("input[name=select_segment]").val() === "True") {
        clickHandler = selectSegment;
        $("#select-word").removeClass("active");
        $("#select-segment").addClass("active");
    }

    $(".labels-field").select2({tags: false});
    $(".labels-field-tags").select2({tags: true});

    $(".word").each(function() {
        $(this).qtip({
            content: {
                text: $(this).next(".tooltiptext")
            }
        });
    });

    $(".tooltiptext").hide();

    $("select[name=words]").parent().hide();
});
