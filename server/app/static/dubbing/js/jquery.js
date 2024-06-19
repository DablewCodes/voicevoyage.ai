var $owl = $('.owl-carousel');

$owl.children().each( function( index ) {
  $(this).attr( 'data-position', index ); // NB: .attr() instead of .data()
});

$owl.owlCarousel({
  center: true,
  items: 5,
});

$(document).on('click', '.owl-item>div', function() {
  // see https://owlcarousel2.github.io/OwlCarousel2/docs/api-events.html#to-owl-carousel
  var $speed = 300;  // in ms
  $owl.trigger('to.owl.carousel', [$(this).data( 'position' ), $speed] );
});

var socket = io();

// Listen for messages to move the carousel
socket.on('processing_update', function(msg) {
  var index = parseInt(msg) - 1; // Convert message to 0-based index
  var $speed = 300;  // Animation speed in ms
  console.log(index)
  $owl.trigger('to.owl.carousel', [index, $speed]);
}); 