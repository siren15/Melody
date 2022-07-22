var changebtn = document.getElementById("changebtn");
var inputbtn = document.getElementById("imageinput");
var backgroundimg = document.getElementById("bg");
var uploadUrl = document.getElementById('uploadurl').value;
var obgurl = document.getElementById('obgurl').value;
var cropperimage = document.getElementById("cropimage");
var $modal = $('#CropModal');
var cropper = null;
var defaultImageURL = obgurl;
var guildID = document.getElementById('guildID').value;
var memberID = document.getElementById('memberID').value;
var defaultBG = document.getElementById('defaultBG').value;

changebtn.addEventListener("click", function() {
  inputbtn.click();
});
inputbtn.addEventListener("change", function(event) {
  inputimage = event.target.files[0];
  if (inputimage.size > 8388608) {
    inputimage = null;
    $('#fileSizeErrorAlert').show();
    
    setTimeout(function () {
      $('#fileSizeErrorAlert').hide();
    }, 5000);
    return;
  };
  // cropperimage.src = URL.createObjectURL(inputimage);
  $modal.modal('show');
});
$modal.on('shown.bs.modal', function () {
  cropOptions = {
    viewport: {
      width: 382,
      height: 174,
      type: 'square'
    },
    boundary: {
      width: 382,
      height: 174,
    },
    showZoomer: false,
  }
  if (cropper == null) {
    cropper = new Croppie(cropperimage, cropOptions);
    cropper.bind({
      url: URL.createObjectURL(inputimage)
    });
  }
  else {
    cropperimage.innerHTML = "";
    cropperimage.classList.remove("croppie-container");
    cropper = new Croppie(cropperimage, cropOptions);
    cropper.bind({
      url: URL.createObjectURL(inputimage)
    });
  };
});
$('#crop').on('click', function () {
  $('#saveAlert').show();
  cropper.result({
    type: 'blob',
    size:{
      width:956,
      height:435
    },
    format: 'png',
    quality: 1,
    circle: false,
  }).then(function(blob) {
    croppedImageURL = URL.createObjectURL(blob);
    backgroundimg.src = croppedImageURL;
    $modal.modal('hide');
    $('#savebtn').on('click', function(){
      var myform = document.getElementById('imageform');
      var form = new FormData(myform);
      form.append('guild_id', guildID);
      form.append('member_id', memberID);
      form.append('image', blob, inputimage.name);
      $.ajax({
        method: 'POST',
        url: uploadUrl,
        data: form,
        processData: false,
        contentType: false,
        success: function(data) {
          $('#progressAlert').hide();
          defaultImageURL = croppedImageURL;
          cropperimage.innerHTML = "";
          cropperimage.classList.remove("croppie-container");
          inputimage = null;
          inputbtn.value = null;
          form.delete('image');
          $('#saveAlert').hide();
          $('#successAlert').show();
          setTimeout(function () {
            $('#successAlert').hide();
          }, 5000);
        },
        error: function(data) {
          $('#progressAlert').hide();
          cropperimage.innerHTML = "";
          cropperimage.classList.remove("croppie-container");
          inputimage = null;
          inputbtn.value = null;
          form.delete('image');
          $('#saveAlert').hide();
          $('#errorAlert').show();
          setTimeout(function () {
            $('#errorAlert').hide();
          }, 5000);
        },
        beforeSend: function() {
          $('#saveAlert').hide();
          $('#progressAlert').show();
        }
      });
    });
  });
});

$('#cropCancel').on('click', function () {
  cropperimage.innerHTML = "";
  cropperimage.classList.remove("croppie-container");
  $modal.modal('hide');
  inputimage = null;
  inputbtn.value = null;
});
$('#cancelbtn').on('click', function () {
  cropperimage.innerHTML = "";
  cropperimage.classList.remove("croppie-container");
  $('#saveAlert').hide();
  inputimage = null;
  inputbtn.value = null;
  backgroundimg.src = defaultImageURL;
});

$('#resetButton').on('click', function () {
  $('#resetSaveAlert').show();
  backgroundimg.src = defaultBG;
  $('#resetSaveButton').on('click', function(){
    $('#resetSaveAlert').hide();
    $('#progressAlert').show();
    var resetURL = document.getElementById('reseturl').value;
    var resetForm = document.getElementById('resetForm');
    var resetFormData = new FormData(resetForm);
    resetFormData.append('guild_id', guildID);
    resetFormData.append('member_id', memberID);
    $.ajax({
      method: 'POST',
      url: resetURL,
      data: resetFormData,
      processData: false,
      contentType: false, 
    })
    .then(function(data){
      $('#progressAlert').hide();
      $('#resetSuccessAlert').show();
      resetFormData.delete('guild_id');
      resetFormData.delete('member_id');
      setTimeout(function () {
        $('#resetSuccessAlert').hide();
      }, 5000);
    })
    .catch(function(data){
      backgroundimg.src = defaultImageURL;
      $('#progressAlert').hide();
      $('#resetErrorAlert').show();
      resetFormData.delete('guild_id');
      resetFormData.delete('member_id');
      setTimeout(function () {
        $('#resetErrorAlert').hide();
      }, 5000);
    });
  });
  $('#resetCancelButton').on('click', function(){
    $('#resetSaveAlert').hide();
    backgroundimg.src = defaultImageURL;
  });
});