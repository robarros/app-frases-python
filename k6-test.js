import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter } from 'k6/metrics';

// Métricas personalizadas para cada endpoint
const endpointCounters = {
    frases: new Counter('endpoint_frases_count'),
    root: new Counter('endpoint_root_count'),
    error: new Counter('endpoint_error_count'),
};

export const options = {
    scenarios: {
        constant_rate: {
            executor: 'constant-arrival-rate',
            rate: 10, // 10 requisições por segundo
            timeUnit: '1s', // tempo em que a taxa é aplicada
            duration: '20s', // 5 minutos
            preAllocatedVUs: 5, // VUs pré-alocados
            maxVUs: 100, // Máximo de VUs se necessário
        },
    },
    thresholds: {
        http_req_duration: ['p(90)<400', 'p(95)<500'], // 90% das requisições < 400ms, 95% < 500ms
        // http_req_failed removido pois o endpoint /error retorna erro propositalmente
    },
};

const endpoints = [
    'https://frases.virtualti.net',
    'https://frases.virtualti.net/frases',
    'https://frases.virtualti.net/error',
];

export default function () {
    // Seleciona um endpoint aleatório para cada requisição
    const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];

    const response = http.get(endpoint);

    // Incrementa contador do endpoint
    if (endpoint.includes('/frases')) {
        endpointCounters.frases.add(1);
    } else if (endpoint.includes('/error')) {
        endpointCounters.error.add(1);
    } else {
        endpointCounters.root.add(1);
    }

    // Log detalhado
    console.log(`[${new Date().toISOString()}] ${endpoint} - Status: ${response.status} - Tempo: ${response.timings.duration.toFixed(2)}ms`);

    check(response, {
        'status é 200 ou 500': (r) => r.status === 200 || r.status === 500,
        'tempo de resposta < 1s': (r) => r.timings.duration < 1000,
    });
}
