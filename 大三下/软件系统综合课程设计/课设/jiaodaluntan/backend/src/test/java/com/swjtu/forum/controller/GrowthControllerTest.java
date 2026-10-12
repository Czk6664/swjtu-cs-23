package com.swjtu.forum.controller;

import com.swjtu.forum.entity.RewardItem;
import com.swjtu.forum.exception.GlobalExceptionHandler;
import com.swjtu.forum.service.GrowthDiscoveryService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.List;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@ExtendWith(MockitoExtension.class)
class GrowthControllerTest {

    private MockMvc mockMvc;

    @Mock
    private GrowthDiscoveryService growthDiscoveryService;

    @BeforeEach
    void setUp() {
        GrowthController controller = new GrowthController(growthDiscoveryService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller)
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    void rewardsListIsPublic() throws Exception {
        RewardItem reward = new RewardItem();
        reward.setId(1L);
        reward.setName("笔记本");
        reward.setCostPoints(100);

        when(growthDiscoveryService.listActiveRewards()).thenReturn(List.of(reward));

        mockMvc.perform(get("/growth/rewards"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data[0].name").value("笔记本"));
    }
}
