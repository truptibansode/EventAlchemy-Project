const testimonials = [  { text: "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Aut voluptatum et esse laborum aperiamquod, soluta nihil veritatis ad consectetur, minus earum culpa animi eveniet nam voluptatem repudiandae impedit sapiente?", author: "Carla Carson" },  { text: "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Aut voluptatum et esse laborum aperiamquod, soluta nihil veritatis ad consectetur, minus earum culpa animi eveniet nam voluptatem repudiandae impedit sapiente?", author: "Jane Smith" },  { text: "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Aut voluptatum et esse laborum aperiamquod, soluta nihil veritatis ad consectetur, minus earum culpa animi eveniet nam voluptatem repudiandae impedit sapiente?", author: "John Doe" }, {text:"Lorem ipsum dolor sit amet, consectetur adipisicing elit. Aut voluptatum et esse laborum aperiamquod, soluta nihil veritatis ad consectetur, minus earum culpa animi eveniet nam voluptatem repudiandae impedit sapiente?", author: "Maya Patil"}];
let currentTestimonial = 0;
const testimonialElem = document.getElementById("testimonial");
const authorElem = document.getElementById("author");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");

function showTestimonial() {
  testimonialElem.innerText = testimonials[currentTestimonial].text;
  authorElem.innerText = testimonials[currentTestimonial].author;
}
function prevTestimonial() {
  currentTestimonial = (currentTestimonial === 0) ? testimonials.length - 1 : currentTestimonial - 1;
  showTestimonial();
}
function nextTestimonial() {
  currentTestimonial = (currentTestimonial === testimonials.length - 1) ? 0 : currentTestimonial + 1;
  showTestimonial();
}

prevBtn.addEventListener("click", prevTestimonial);
nextBtn.addEventListener("click", nextTestimonial);