// Get the modal
var modal = document.getElementById("ModalViewer");

// Get the image and insert it inside the modal
var modalImg = document.getElementById("modal-img");
var imgArray = document.getElementsByClassName("gallery-img")
for (var i = 0; i < imgArray.length; i++) {
  var img = imgArray[i];
  img.onclick = function(){
    modal.style.display = "block";
    modalImg.src = this.src;
    modalImg.onclick = function() {
      modal.style.display = "none";
    }
  }
}

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

modal.onclick = function() {
  modal.style.display = "none";
}
/* based on https://www.w3schools.com/howto/howto_css_modal_images.asp */
