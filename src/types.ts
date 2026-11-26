export type ElementKind='headline'|'body'|'metric'|'icon'|'shape'|'label';
export type MotionElement={id:string;kind:ElementKind;text:string;x:number;y:number;width:number;color:string;font_size:number;weight:number;animation:string;delay:number;accent?:string|null;asset_id?:string|null;asset_data?:string|null};
export type Scene={id:string;title:string;duration:number;description:string;narration:string;transition:string;background:string;background_asset?:string|null;background_data?:string|null;elements:MotionElement[]};
export type ProjectSpec={title:string;prompt:string;language:string;aspect_ratio:'16:9'|'9:16'|'1:1';fps:number;width:number;height:number;palette:string[];scenes:Scene[]};
export type Project={id:string;spec:ProjectSpec;updated_at:string};
