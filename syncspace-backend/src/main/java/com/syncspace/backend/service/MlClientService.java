package com.syncspace.backend.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.Map;

@Service
public class MlClientService {

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${ml.service.url:http://localhost:8000}")
    private String mlBaseUrl;

    @SuppressWarnings("unchecked")
    public Map<String, Object> parseText(String text) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            Map<String, String> payload = Map.of("text", text);
            var request = new HttpEntity<>(payload, headers);

            String jsonResponse = restTemplate.postForObject(mlBaseUrl + "/parse", request, String.class);
            return jsonResponse != null ? objectMapper.readValue(jsonResponse, Map.class) : new HashMap<>();
        } catch (Exception e) {
            throw new RuntimeException("Gagal menghubungi ML Service (/parse): " + e.getMessage(), e);
        }
    }

    public Map<String, Object> parseVoice(MultipartFile file) {
        return sendMultipart(mlBaseUrl + "/parse-voice", file);
    }

    public Map<String, Object> parseReceipt(MultipartFile file) {
        return sendMultipart(mlBaseUrl + "/parse-receipt", file);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> sendMultipart(String url, MultipartFile file) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            ByteArrayResource resource = new ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() {
                    return (file.getOriginalFilename() != null && !file.getOriginalFilename().isEmpty())
                            ? file.getOriginalFilename()
                            : "upload.tmp";
                }
            };
            body.add("file", resource);

            var requestEntity = new HttpEntity<>(body, headers);
            String jsonResponse = restTemplate.postForObject(url, requestEntity, String.class);
            return jsonResponse != null ? objectMapper.readValue(jsonResponse, Map.class) : new HashMap<>();
        } catch (Exception e) {
            throw new RuntimeException("Gagal mengirim file ke ML Service (" + url + "): " + e.getMessage(), e);
        }
    }
}