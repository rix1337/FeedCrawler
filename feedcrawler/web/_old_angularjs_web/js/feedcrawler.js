$(function () {
    $('[data-toggle="tooltip"]').tooltip()
});



function showSuccess(message) {
    $(".alert-success").html(message).fadeTo(3000, 500).slideUp(500, function () {
        $(".alert-success").slideUp(500);
    });
}

function showInfo(message) {
    $(".alert-info").html(message).fadeTo(10000, 500).slideUp(500, function () {
        $(".alert-info").slideUp(500);
    });
}

function showInfoLong(message) {
    $(".alert-info").html(message).show();
}

function showDanger(message) {
    $(".alert-danger").html(message).fadeTo(5000, 500).slideUp(500, function () {
        $(".alert-danger").slideUp(500);
    });
}
