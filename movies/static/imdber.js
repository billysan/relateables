
function search_button_loading(dots_count) {
  $("#movie_search").text('just a sec' + '.'.repeat(dots_count));
  setTimeout(search_button_loading, 180, (dots_count + 1) % 4);
}

$(function() {

  $( "#movie_url" ).autocomplete({
    source: function (request, response) {
      $.get("/imdber?term=" + request.term, function (data) {

        var aso = JSON.parse(data.replace(/'/g, '"'));

        var y = $.map(aso.results, function (value, key) {
          return {
            label: value,
            value: key
          };
        });

        response(y);

      });
    },
    minLength: 2,
    delay: 100,
    select: function( event, ui ) {
      search_button_loading(1);
      $( "#movie_url" ).fadeOut();
      setTimeout(function() { $("#movie_search").click(); }, 2000);
    }
  } );
} );

$(document).ready(function() { $("#movie_search_container").fadeIn(); });
