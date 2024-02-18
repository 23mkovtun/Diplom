$(document).ready(function() {
    $(".update-status-btn").click(function() {
        var orderId = $(this).data("order-id");
        var nextStatus = $(this).data("next-status");
        $.ajax({
            url: "/update_order_status/",
            method: "POST",
            data: { order_id: orderId, next_status: nextStatus },
            success: function(response) {
                alert("Статус заказа успешно обновлен");
                // Обновляем статус на странице без перезагрузки
                // Это зависит от вашей конкретной реализации
            },
            error: function(xhr, status, error) {
                alert("Ошибка при обновлении статуса заказа");
            }
        });
    });
});
