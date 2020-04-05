var toggler = document.getElementsByClassName("pointer");
console.log(toggler)
var i;

for (i = 0; i < toggler.length; i++) {
    console.log("here")
    toggler[i].addEventListener("click", function() {
        console.log("clicked")
        this.parentElement.querySelector(".children").classList.toggle("active");
        this.classList.toggle("pointer-down");
    });
}