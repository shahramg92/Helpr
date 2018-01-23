var basicTimeline = anime.timeline({
  autoplay: false
});

var pathEls = $(".check");
for (var i = 0; i < pathEls.length; i++) {
  var pathEl = pathEls[i];
  var offset = anime.setDashoffset(pathEl);
  pathEl.setAttribute("stroke-dashoffset", offset);
}

basicTimeline
  .add({
    targets: ".text",
    duration: 1,
    opacity: "0"
  })
  .add({
    targets: ".button",
    duration: 1300,
    height: 20,
    width: 300,
    backgroundColor: "#2B2D2F",
    border: "0",
    borderRadius: 100
  })
  .add({
    targets: ".progress-bar",
    duration: 2000,
    width: 800,
    easing: "linear"
  })
  .add({
    targets: ".button",
    width: 0,
    duration: 1
  })
  .add({
    targets: ".progress-bar",
    width: 80,
    height: 80,
    delay: 0,
    duration: 750,
    borderRadius: 80,
    backgroundColor: "#71DFBE",
  })
  .add({
    targets: 'svg',
    zIndex: 10
  })
  .add({
    targets: pathEl,
    strokeDashoffset: [offset, 0],
    duration: 200,
    easing: "easeInOutSine",
  });


function submit_form () {
  var form = $("#form").get(0);

  if (form.checkValidity()) {
    basicTimeline.play();
    setTimeout(function(){form.submit();}, 6000)

  } else {
    swal(
  'Oops... Something went wrong!',
  'Please re-check your form',
  'error'
)};
}
