console.log("Sanity check!");
let stripe;
fetch("/config/")
.then((result) => { return result.json(); })
.then((data) => {
  stripe = Stripe(data.publicKey);
});
// $('body').on('click','.select-plan', function () {
//     let plan_id = $(this).attr('data-id');
//     $('#plan_id').val(plan_id);
//     $('.purchase-plan').removeClass('active');
//     $(this).closest('.purchase-plan').addClass('active');
//     $('.revise-box').show();
// });
$('body').on('click','.purchase', function () {
     let plan_id = $(this).attr('data-id');
     if(!plan_id){
         return
     }
     fetch("/create-checkout-session/?plan_id="+plan_id)
    .then((result) => { return result.json();})
    .then((data) => {
      if(data.email){
        alert("メールアドレスをご記入ください！");
        window.location = '/authorization/profile/';
      }
      if(data.error){
        alert("stripe接続状態を確認してください！");
        window.location = '/payment/';
      }
      if(data.success){
        window.location = '/payment/success?plan_id=1';
      }else{          
        return stripe.redirectToCheckout({sessionId: data.sessionId})
      }
    })
    .then((res) => {      
      console.log(res);
    });
})