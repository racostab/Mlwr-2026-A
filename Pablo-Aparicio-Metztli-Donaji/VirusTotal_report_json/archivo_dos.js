OkHttpClient client = new OkHttpClient();

Request request = new Request.Builder()
  .url("https://www.virustotal.com/api/v3/files/1dc34e167c6d1b66172f90288b241bc7")
  .get()
  .addHeader("accept", "application/json")
  .addHeader("x-apikey", "899adc0d8237c25d9500293250c4b9fd15a269ac393c8ac16d8bfd10ac9fa932")
  .build();

Response response = client.newCall(request).execute();
