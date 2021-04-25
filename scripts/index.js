<script> function sendcodejs() {
                  const em = document.querySelector('#emailf').value;
                  const pa = document.querySelector('#passwordf').value;
                  const request = new XMLHttpRequest();
                  request.open('POST', '/code' + '/' + em + '/' + pa);
                  request.onload = () => {
                  const data = JSON.parse(request.responseText);
                  if (not data.result){
                  alert('Введен некорректный адрес.');
                };
            };
                  const data = new FormData();
                  request.send(data);
                  return false;

};</script>