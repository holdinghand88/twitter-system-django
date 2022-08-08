//js for mobile nav
const navAction = document.querySelector(".sc-cyjdnp");
const mobileNav = document.querySelector(".sidenav-right.mobile");
const mobileShow = document.querySelector(".mobile-menu-show");
const mobileHide = document.querySelector(".mobile-menu-hide");

navAction.addEventListener("click", (e) => {
  mobileNav.classList.toggle("show");
  mobileHide.classList.toggle("d-none");
  mobileShow.classList.toggle("d-none");
});

// const inner = document.querySelectorAll(".sidenav-right > .inner");
// const listItem = document.querySelectorAll(".sidenav-left > .list");
// const analytics = document.getElementById("analytics");
// const inbox = document.getElementById("inbox");
// const follower = document.getElementById("follower");
// const tweet = document.getElementById("tweet");
// document.querySelector(".sidenav-left").addEventListener("click", (e) => {
//   const clicked = e.target.closest(".list");

//   listItem.forEach((el) => {
//     el.classList.remove("active");
//     clicked.classList.add("active");
//   });
//   if (clicked.id == "") return;

//   if (clicked) {
//     inner.forEach((el) => {
//       el.classList.remove("d-none");
//     });

//     if (clicked.id.includes("analytics")) {
//       analytics.classList.remove("d-none");
//     } else {
//       analytics.classList.add("d-none");
//     }
//     if (clicked.id.includes("inbox")) {
//       inbox.classList.remove("d-none");
//     } else {
//       inbox.classList.add("d-none");
//     }

//     if (clicked.id.includes("follower")) {
//       follower.classList.remove("d-none");
//     } else {
//       follower.classList.add("d-none");
//     }

//     if (clicked.id.includes("tweet")) {
//       tweet.classList.remove("d-none");
//     } else {
//       tweet.classList.add("d-none");
//     }
//   }
// });
